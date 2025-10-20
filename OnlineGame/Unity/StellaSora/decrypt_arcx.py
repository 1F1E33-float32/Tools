from __future__ import annotations

import argparse
import hashlib
import os
import struct
from dataclasses import dataclass
from typing import BinaryIO, List, Optional

import lz4.block

MAGIC_U32_LE = 0x5241421A  # bytes: 1A 42 41 52
HEADER_SIZE_BYTES = 0x20
ENTRY_RECORD_SIZE = 8 + 4 + 4 + 4  # hash(8) + block_offset(4) + origin_size(4) + size(4)
BLOCK_SHIFT = 12  # block_offset << 0xC


@dataclass
class ArchiveHeader:
    version: int
    header_flag: int
    block_flag: int
    entries_origin_size: int
    entries_size: int
    block_entries: int
    reserved_1c: int


@dataclass
class ArchiveEntry:
    hash64: int
    block_offset: int
    origin_size: int
    size: int


def read_exact(stream: BinaryIO, size: int) -> bytes:
    data = stream.read(size)
    if data is None or len(data) != size:
        raise EOFError(f"Expected {size} bytes, got {0 if data is None else len(data)}")
    return data


def parse_header(stream: BinaryIO) -> ArchiveHeader:
    stream.seek(0, os.SEEK_SET)
    raw = read_exact(stream, HEADER_SIZE_BYTES)
    magic_u32 = struct.unpack_from("<I", raw, 0)[0]
    if magic_u32 != MAGIC_U32_LE:
        raise ValueError(f"Bad magic: got 0x{magic_u32:08X}, expected 0x{MAGIC_U32_LE:08X} (bytes {raw[:4].hex()})")

    version, header_flag, block_flag, entries_origin_size, entries_size, block_entries, reserved = struct.unpack_from("<7I", raw, 4)
    return ArchiveHeader(
        version=version,
        header_flag=header_flag,
        block_flag=block_flag,
        entries_origin_size=entries_origin_size,
        entries_size=entries_size,
        block_entries=block_entries,
        reserved_1c=reserved,
    )


def decode_stream(
    stream: BinaryIO,
    offset: int,
    is_compressed: bool,
    is_encrypted: bool,
    origin_size: int,
    size: int,
    xor_key: Optional[bytes],
) -> bytes:
    stream.seek(offset, os.SEEK_SET)

    if is_compressed and is_encrypted:
        raise ValueError("同时加密和压缩的文件不支持读取")

    if not is_compressed:
        if is_encrypted:
            if not xor_key:
                raise ValueError("需要提供--pack-key")
            data = read_exact(stream, origin_size)
            out = bytearray(data)
            for i in range(len(out)):
                out[i] ^= xor_key[i % len(xor_key)]
            return bytes(out)
        return read_exact(stream, origin_size)

    comp = read_exact(stream, size)
    return lz4.block.decompress(comp, uncompressed_size=origin_size)


def parse_entries_table(data: bytes, expected_count: int) -> List[ArchiveEntry]:
    if len(data) % ENTRY_RECORD_SIZE != 0:
        raise ValueError(f"Entries table size {len(data)} is not a multiple of {ENTRY_RECORD_SIZE}")
    count = len(data) // ENTRY_RECORD_SIZE
    if count != expected_count:
        raise ValueError("")
    entries: List[ArchiveEntry] = []
    off = 0
    for _ in range(count):
        hash64 = struct.unpack_from("<Q", data, off)[0]
        block_offset, origin_size, size = struct.unpack_from("<III", data, off + 8)
        entries.append(ArchiveEntry(hash64=hash64, block_offset=block_offset, origin_size=origin_size, size=size))
        off += ENTRY_RECORD_SIZE
    return entries


def _parse_int_auto(x) -> int:
    if isinstance(x, int):
        return x
    if x is None:
        raise ValueError("value is None")
    return int(str(x), 0)


def Xta_XTA_FK(k: bytes) -> bytes:
    if len(k) == 16:
        return k
    if len(k) < 16:
        return k + b"\x00" * (16 - len(k))
    return k[:16]


def Xta_XTA_TU3A(d: bytes, includeLength: bool) -> List[int]:
    size = len(d)
    n = (size + 3) // 4
    if includeLength:
        n += 1
    v: List[int] = [0] * n
    for i in range(size):
        v[i >> 2] |= d[i] << (8 * (i & 3))
    if includeLength:
        v[-1] = size
    return v


def Xta_XTA_TBA(v: List[int], includeLength: bool) -> bytes:
    if not v:
        return b""
    total = 4 * len(v)
    if includeLength:
        m = v[-1]
        if not (0 <= m <= total - 4):
            return b""
        out_len = m
    else:
        out_len = total
    out = bytearray(out_len)
    idx = 0
    for w in v:
        for s in range(4):
            if idx >= out_len:
                return bytes(out)
            out[idx] = (w >> (8 * s)) & 0xFF
            idx += 1
    return bytes(out)


def Xta_XTA_M(sum_: int, y: int, z: int, p: int, e: int, k_words: List[int]) -> int:
    return ((y ^ sum_) + (k_words[(e ^ (p & 3)) & 3] ^ z)) ^ (((z << 4) ^ (y >> 3)) + ((z >> 5) ^ (y << 2)))


def Xta_XTA__D(v: List[int], k_words: List[int]) -> List[int]:
    n = len(v)
    if n < 2:
        return v
    delta = 0x9E3779B9
    q = 6 + 52 // n
    sum_ = (q * delta) & 0xFFFFFFFF
    z = v[0]
    while sum_ != 0:
        e = (sum_ >> 2) & 3
        for p in range(n - 1, 0, -1):
            y = v[p - 1]
            v[p] = (v[p] - Xta_XTA_M(sum_, z, y, p, e, k_words)) & 0xFFFFFFFF
            z = v[p]
        y = v[n - 1]
        v[0] = (v[0] - Xta_XTA_M(sum_, z, y, 0, e, k_words)) & 0xFFFFFFFF
        z = v[0]
        sum_ = (sum_ - delta) & 0xFFFFFFFF
    return v


def Xta_XTA_D(d: bytes, k: bytes) -> bytes:
    if not d:
        return d
    k_fixed = Xta_XTA_FK(k)
    v = Xta_XTA_TU3A(d, False)
    k_words = Xta_XTA_TU3A(k_fixed, False)
    v_dec = Xta_XTA__D(v, k_words)
    return Xta_XTA_TBA(v_dec, True)


def AC_H_C(input_bytes: bytes) -> bytes:
    return hashlib.md5(input_bytes).digest()


def AC_get___CK(kx: int, ky: int) -> bytes:
    prod32 = (kx * ky) & 0xFFFFFFFF
    return AC_H_C(struct.pack("<I", prod32))


def AC_DA(input_bytes: bytes, ck: bytes) -> bytes:
    return Xta_XTA_D(input_bytes, ck)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=r"C:\Users\bfloat16\Downloads\YostarGames\StellaSora_CN\Persistent_Store\Tables\data.arcx")
    parser.add_argument("--output", default=r"C:\Users\bfloat16\Downloads\YostarGames\StellaSora_CN\Persistent_Store\Tables\data")
    parser.add_argument("--pack-key", default=r"&^^%#$#_$!@![]<_>?GHBFR_1153SDR_")
    parser.add_argument("--kx", type=str, default=0xFF, help="AC.__kx integer (decimal or 0x-hex)")
    parser.add_argument("--ky", type=str, default=0xFF, help="AC.__ky integer (decimal or 0x-hex)")
    args = parser.parse_args()

    xor_key: Optional[bytes] = None
    if args.pack_key:
        xor_key = args.pack_key.encode("utf-8")

    with open(args.input, "rb") as f:
        header = parse_header(f)

        entries_blob = decode_stream(
            f,
            offset=HEADER_SIZE_BYTES,
            is_compressed=False,
            is_encrypted=bool(header.header_flag & 0x10),
            origin_size=header.entries_origin_size,
            size=header.entries_size,
            xor_key=xor_key if (header.header_flag & 0x10) else None,
        )
        entries = parse_entries_table(entries_blob, header.block_entries)

        print(f"Magic: 0x{MAGIC_U32_LE:08X}")
        print(f"Version: {header.version}")
        print(f"HeaderFlag: 0x{header.header_flag:08X}")
        print(f"BlockFlag:  0x{header.block_flag:08X}  (Compressed={'Y' if header.block_flag & 0x10 else 'N'}, Encrypted={'Y' if header.block_flag & 0x100 else 'N'})")
        print(f"Entries: {len(entries)} (header={header.block_entries})")
        print(f"EntriesTable: origin_size={header.entries_origin_size} size={header.entries_size}")

        os.makedirs(args.output, exist_ok=True)

        ck: Optional[bytes] = None
        if args.kx is not None and args.ky is not None:
            try:
                kx = _parse_int_auto(args.kx)
                ky = _parse_int_auto(args.ky)
            except Exception as exc:
                raise SystemExit(f"Invalid --kx/--ky: {exc}")
            ck = AC_get___CK(kx, ky)
            print(f"Derived CK (AC::get___CK): {ck.hex()}")

        total_origin = 0
        total_comp = 0
        for i, e in enumerate(entries):
            file_offset = e.block_offset << BLOCK_SHIFT
            data = decode_stream(
                f,
                offset=file_offset,
                is_compressed=bool(header.block_flag & 0x10),
                is_encrypted=bool(header.block_flag & 0x100),
                origin_size=e.origin_size,
                size=e.size,
                xor_key=xor_key if (header.block_flag & 0x100) else None,
            )

            out_name = f"{i:05d}_{e.hash64:016x}.lua"
            out_path = os.path.join(args.output, out_name)
            # Optional second-stage (AC::DA) using XXTEA with CK
            if ck is not None and data:
                data = AC_DA(data, ck)
            with open(out_path, "wb") as w:
                w.write(data)
            print(f"Wrote {out_name} ({len(data)} bytes) from off=0x{file_offset:08X}")
            total_origin += e.origin_size
            total_comp += e.size

        print(f"Totals: origin_sum={total_origin} bytes, comp_sum={total_comp} bytes; file_size={os.path.getsize(args.input)} bytes")
