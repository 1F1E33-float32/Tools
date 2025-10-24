import argparse
import json
import zlib
from pathlib import Path

from cs2_utils import CS2_MAIN_OPCODES, Reader, extract_message, is_command_line, is_message_text, tokenize_spaces


def _decode_cstx_with_meta(data):
    r = Reader(data)
    header = r.read(4)
    if header != b"CSTX":
        raise ValueError("bad CSTX header")
    original_len = r.read_int_le()
    comp_len = r.read_int_le()
    if original_len <= 0:
        raise ValueError("invalid original length")
    if comp_len == 0:
        payload = r.read(original_len)
        meta = {"header": "CSTX", "encoding": {"mode": "raw", "original_len": original_len, "compressed_len": 0}}
        return payload, meta
    mode = r.read_int_le()  # 1 = zlib(deflate)
    comp = r.read(comp_len)
    try:
        payload = zlib.decompress(comp, -zlib.MAX_WBITS)
    except Exception:
        payload = zlib.decompress(comp)
    meta = {"header": "CSTX", "encoding": {"mode": "zlib", "original_len": original_len, "compressed_len": comp_len, "mode_id": mode}}
    return payload, meta


def _parse_payload_to_blocks(payload_bytes):
    r = Reader(payload_bytes)
    block_count = r.read_int_le()
    blocks = []
    total_lines = 0
    for _ in range(block_count):
        n_lines = r.read_varint()
        lines = [r.read_string() for _ in range(n_lines)]
        total_lines += n_lines
        items = []
        for li, line in enumerate(lines):
            kind = "command" if is_command_line(line) else ("message" if is_message_text(line) else "blank")
            entry = {"index": li, "kind": kind}
            if kind == "command":
                toks = tokenize_spaces(line)
                entry.update(
                    {
                        "opcode": toks[0] if toks else None,
                        "args": toks[1:] if len(toks) > 1 else [],
                        "is_known": (toks[0] in CS2_MAIN_OPCODES) if toks else None,
                    }
                )
            elif kind == "message":
                msg = extract_message(line)
                entry.update(msg or {})
            items.append(entry)
        blocks.append({"lineCount": n_lines, "lines": lines, "items": items})
    return block_count, total_lines, blocks


def parse_cstx_to_dict(data):
    payload, meta = _decode_cstx_with_meta(data)
    block_count, total_lines, blocks = _parse_payload_to_blocks(payload)
    return {
        **meta,
        "blockCount": block_count,
        "totalLines": total_lines,
        "blocks": blocks,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=r"D:\Fuck_VN\script")
    args = p.parse_args()

    in_path = Path(args.input)
    for fp in in_path.glob("*.cstx"):
        with fp.open("rb") as f:
            data = f.read()
        obj = parse_cstx_to_dict(data)
        out_path = fp.with_suffix(".json")
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
