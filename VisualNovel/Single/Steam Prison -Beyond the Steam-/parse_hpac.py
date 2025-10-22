from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

# HPAC constants (from cctor and Head::Read/Table::Read)
HPAC_ID = 0x43415048  # 'HPAC' little-endian
HPAC_VERSION = 0x10100
HPAC_HEAD_SIZE = 0x20
HPAC_TABLE_SIZE = 0x20


# Minimal HLZS support (ID/version/head-size from cctor and Head::Read)
HLZS_ID = 0x535A4C48  # 'HLZS'
HLZS_VERSION = 0x1000
HLZS_HEAD_SIZE = 0x20
HLZS_DIC_SIZE = 0x1000
HLZS_MAX_LEN = 0x12


def read_u32_le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little", signed=False)


def read_u64_le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 8], "little", signed=False)


def parse_hpac_head(blob: bytes, offset: int = 0) -> Dict[str, int]:
    if len(blob) < offset + HPAC_HEAD_SIZE:
        raise ValueError("HPAC header truncated")
    header_id = read_u32_le(blob, offset + 0)
    version = read_u32_le(blob, offset + 4)
    count = read_u32_le(blob, offset + 8)
    table_offset = read_u32_le(blob, offset + 0x0C)
    name_offset = read_u32_le(blob, offset + 0x10)
    return {
        "id": header_id,
        "version": version,
        "count": count,
        "table_offset": table_offset,
        "name_offset": name_offset,
        "header_size": HPAC_HEAD_SIZE,
    }


def parse_names(blob: bytes, start: int, count: int) -> List[str]:
    names: List[str] = []
    pos = start
    for _ in range(count):
        if pos >= len(blob):
            break
        end = blob.find(b"\x00", pos)
        if end == -1:
            break
        raw = blob[pos:end]
        try:
            s = raw.decode("utf-8", errors="replace")
        except Exception:
            s = raw.decode("latin-1", errors="replace")
        names.append(s)
        pos = end + 1
    return names


def parse_table_entry(blob: bytes, offset: int) -> Dict[str, int]:
    if offset + HPAC_TABLE_SIZE > len(blob):
        raise ValueError("HPAC table entry truncated")
    entry_offset = read_u64_le(blob, offset + 0x00)
    entry_key = read_u32_le(blob, offset + 0x08)
    file_size = read_u32_le(blob, offset + 0x0C)  # compressed size
    melt_size = read_u32_le(blob, offset + 0x10)  # decompressed size
    file_crc = read_u32_le(blob, offset + 0x14)
    melt_crc = read_u32_le(blob, offset + 0x18)
    return {
        "offset": entry_offset,
        "key": entry_key,
        "file_size": file_size,
        "melt_size": melt_size,
        "file_crc": file_crc,
        "melt_crc": melt_crc,
    }


def is_hlzs(data: bytes, offset: int = 0) -> bool:
    return len(data) >= offset + 4 and read_u32_le(data, offset) == HLZS_ID


def lzs_decompress(container: bytes, start_offset: int, expected_output_size: int) -> bytes:
    ring = bytearray(b"\x20" * HLZS_DIC_SIZE)
    rpos = HLZS_DIC_SIZE - HLZS_MAX_LEN
    out = bytearray()
    src = start_offset
    total = len(container)
    while len(out) < expected_output_size and src < total:
        flags = container[src]
        src += 1
        for _ in range(8):
            if len(out) >= expected_output_size or src >= total:
                break
            if flags & 1:
                b = container[src]
                src += 1
                out.append(b)
                ring[rpos] = b
                rpos = (rpos + 1) & (HLZS_DIC_SIZE - 1)
            else:
                if src + 1 >= total:
                    raise ValueError("HLZS backref truncated")
                b1 = container[src]
                b2 = container[src + 1]
                src += 2
                off = b1 | ((b2 & 0xF0) << 4)
                ln = (b2 & 0x0F) + 3
                for i in range(ln):
                    v = ring[(off + i) & (HLZS_DIC_SIZE - 1)]
                    out.append(v)
                    ring[rpos] = v
                    rpos = (rpos + 1) & (HLZS_DIC_SIZE - 1)
                    if len(out) >= expected_output_size:
                        break
            flags >>= 1
    return bytes(out)


def maybe_decompress_chunk(chunk: bytes) -> bytes:
    # HLZS chunk: header + payload
    if is_hlzs(chunk, 0):
        if read_u32_le(chunk, 4) != HLZS_VERSION:
            raise ValueError("HLZS version mismatch in chunk")
        decode_size = read_u32_le(chunk, 12)
        return lzs_decompress(chunk, HLZS_HEAD_SIZE, decode_size)
    # TODO: Add Huffman/LZH if needed; default to raw
    return chunk


def extract_hpac_from_buffers(head_bytes: bytes, data_bytes: bytes, out_dir: Path, json_path: Path | None = None) -> None:
    head = parse_hpac_head(head_bytes, 0)
    if head["id"] != HPAC_ID:
        raise ValueError("Not HPAC (bad ID)")
    if head["version"] != HPAC_VERSION:
        raise ValueError("HPAC version mismatch")

    names = parse_names(head_bytes, head["name_offset"], head["count"]) or []
    tables: List[Dict[str, int]] = []
    # tables are in header buffer starting after head
    off = HPAC_HEAD_SIZE
    for _ in range(head["count"]):
        tables.append(parse_table_entry(head_bytes, off))
        off += HPAC_TABLE_SIZE

    if names and len(names) != len(tables):
        pass

    # optionally write header JSON summary
    if json_path is not None:
        meta = {
            "header": head,
            "names": names,
            "tables": tables,
        }
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, ent in enumerate(tables):
        name = names[idx] if idx < len(names) else f"entry_{idx:05d}"
        chunk_off = ent["offset"]
        comp_size = ent["file_size"]
        if chunk_off + comp_size > len(data_bytes):
            raise ValueError(f"chunk out of range: {name}")
        chunk = data_bytes[chunk_off : chunk_off + comp_size]
        payload = maybe_decompress_chunk(chunk)
        out_path = out_dir / name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(payload)


def extract_hpac(pack_path: Path, out_dir: Path, json_path: Path | None = None) -> None:
    data = pack_path.read_bytes()
    extract_hpac_from_buffers(data, data, out_dir, json_path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse/Extract HPAC pack (.hph+.hpb auto from base path)")
    ap.add_argument("input", help="base path (no ext or .hph/.hpb) to derive pair")
    ap.add_argument("--outdir", default=None, help="output dir (default: base path directory/stem)")
    args = ap.parse_args()
    base = Path(args.input)
    # derive header/data from base
    if base.suffix.lower() == ".hph":
        stem = base.with_suffix("")
        head_path = base
        data_path = stem.with_suffix(".hpb")
        default_outdir = stem
    elif base.suffix.lower() == ".hpb":
        stem = base.with_suffix("")
        head_path = stem.with_suffix(".hph")
        data_path = base
        default_outdir = stem
    else:
        stem = base
        head_path = stem.with_suffix(".hph")
        data_path = stem.with_suffix(".hpb")
        default_outdir = stem
    outdir = Path(args.outdir) if args.outdir else default_outdir
    json_path = stem.with_suffix(".json")
    if not head_path.exists() or not head_path.is_file():
        raise SystemExit(f"missing header file: {head_path}")
    if not data_path.exists() or not data_path.is_file():
        raise SystemExit(f"missing data file: {data_path}")
    head_bytes = head_path.read_bytes()
    data_bytes = data_path.read_bytes()
    extract_hpac_from_buffers(head_bytes, data_bytes, outdir, json_path)


if __name__ == "__main__":
    main()
