from __future__ import annotations

import argparse
import io
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, List

def _read_uint32(f: BinaryIO) -> int:
    data = f.read(4)
    if len(data) != 4:
        raise EOFError("Unexpected end of file while reading uint32")
    return struct.unpack("<I", data)[0]

def _copy_overlapped(buf: bytearray, src: int, dst: int, count: int) -> None:
    for _ in range(count):
        buf.append(buf[src])
        src += 1

ZLC2_SIGNATURE = 0x32434C5A  # 'ZLC2' little-endian

def _decompress_zlc2(data: bytes) -> bytes:
    if len(data) < 8 or struct.unpack("<I", data[:4])[0] != ZLC2_SIGNATURE:
        return data

    src = 8  # skip signature & output size (already read below)
    output_size = struct.unpack("<I", data[4:8])[0]
    out = bytearray()

    while src < len(data) and len(out) < output_size:
        ctl = data[src]
        src += 1
        mask = 0x80
        while mask and src < len(data) and len(out) < output_size:
            if ctl & mask:
                if src + 2 > len(data):
                    raise ValueError("Malformed ZLC2 stream")
                offset = data[src]
                count = data[src + 1]
                src += 2
                offset |= (count & 0xF0) << 4
                count = (count & 0x0F) + 3
                if offset == 0:
                    offset = 4096
                if offset > len(out):
                    raise ValueError("Invalid back‑reference in ZLC2 stream")
                _copy_overlapped(out, len(out) - offset, len(out), count)
            else:
                out.append(data[src])
                src += 1
            mask >>= 1
    return bytes(out[:output_size])

@dataclass
class FpkEntry:
    name: str
    offset: int
    size: int

    def get_data(self, fp: BinaryIO) -> bytes:
        fp.seek(self.offset)
        raw = fp.read(self.size)
        prev = raw
        while True:
            decomp = _decompress_zlc2(prev)
            if decomp == prev:
                return decomp
            prev = decomp

class FpkArchive:
    PLAIN_NAME_SIZES = (0x10, 0x18)

    def __init__(self, fp: BinaryIO):
        self._fp = fp
        self.entries: List[FpkEntry] = []
        self._parse_index()

    def list(self) -> List[FpkEntry]:
        return self.entries

    def extract_to(self, dest_root: Path) -> None:
        dest_root.mkdir(parents=True, exist_ok=True)
        for entry in self.entries:
            out_path = dest_root / entry.name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as out_fp:
                out_fp.write(entry.get_data(self._fp))

    def _parse_index(self) -> None:
        self._fp.seek(0, io.SEEK_END)
        file_size = self._fp.tell()
        self._fp.seek(0)
        count_raw = struct.unpack("<i", self._fp.read(4))[0]

        if count_raw < 0:
            count = count_raw & 0x7FFF_FFFF
            self.entries = self._read_encrypted_index(count, file_size)
        else:
            count = count_raw
            self.entries = self._read_plain_index(count)

    def _read_encrypted_index(self, count: int, file_size: int) -> List[FpkEntry]:
        if count <= 0:
            raise ValueError("Invalid entry count (encrypted index)")

        self._fp.seek(file_size - 8)
        key = self._fp.read(4)
        index_offset = _read_uint32(self._fp)
        if not (4 <= index_offset < file_size - 8):
            raise ValueError("Bad index offset")

        name_size = 0x18
        stride = 12 + name_size
        total_size = count * stride

        self._fp.seek(index_offset)
        enc = bytearray(self._fp.read(total_size))
        if len(enc) != total_size:
            raise EOFError("Could not read full encrypted index")

        for i in range(total_size):
            enc[i] ^= key[i & 3]

        entries: List[FpkEntry] = []
        pos = 0
        for _ in range(count):
            offset, size = struct.unpack_from("<II", enc, pos)
            raw_name = enc[pos + 8 : pos + 8 + name_size]
            pos += stride
            name = raw_name.split(b"\0", 1)[0].decode("shift_jis", errors="ignore").strip()
            if not name:
                raise ValueError("Empty entry name in encrypted index")
            entries.append(FpkEntry(name, offset, size))
        return entries

    def _read_plain_index(self, count: int) -> List[FpkEntry]:
        base = 4
        for name_size in self.PLAIN_NAME_SIZES:
            try:
                return self._try_plain_index(count, name_size, base)
            except Exception:
                continue
        raise ValueError("Unable to parse plain index with known name sizes")

    def _try_plain_index(self, count: int, name_size: int, base: int) -> List[FpkEntry]:
        stride = 8 + name_size
        self._fp.seek(base)
        data = self._fp.read(count * stride)
        if len(data) != count * stride:
            raise EOFError("Could not read full index")

        data_start = base + count * stride
        entries: List[FpkEntry] = []
        pos = 0
        for _ in range(count):
            offset, size = struct.unpack_from("<II", data, pos)
            raw_name = data[pos + 8 : pos + 8 + name_size]
            pos += stride
            name = raw_name.split(b"\0", 1)[0].decode("cp932", errors="ignore").strip()
            if not name:
                raise ValueError("Empty entry name in plain index")
            if offset < data_start:
                raise ValueError("Entry offset within index (wrong name size)")
            entries.append(FpkEntry(name, offset, size))
        return entries

def _classify_archive(file_path: Path) -> tuple[Path | None, str]:
    fname = file_path.stem  # without .fpk
    lower = fname.lower()

    # data.fpk → script/
    if lower == "data":
        return Path("script"), "data archive"

    # CV*.fpk pattern
    if lower.startswith("cv"):
        rest = fname[2:]
        dest_part = rest.split("_", 1)[0]  # before first underscore (if any)
        return Path("voice") / dest_part, "voice archive"

    return None, "unrecognised pattern"

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--indir", type=Path, default=Path(r"D:\GAL\2025_06\WANNABE→CREATORS 2"))
    p.add_argument("--outdir", type=Path, default=Path(r"D:\Fuck_galgame"))
    args = p.parse_args()

    if not args.indir.is_dir():
        sys.exit(f"Error: '{args.indir}' is not a directory")

    out_root = args.outdir or args.indir.with_name(args.indir.name + "_extract")
    out_root.mkdir(parents=True, exist_ok=True)

    fpk_files = sorted(args.indir.glob("*.fpk"))
    if not fpk_files:
        sys.exit("No .fpk files found in input directory")

    for fpk in fpk_files:
        subdir, reason = _classify_archive(fpk)
        if subdir is None:
            print(f"[skip] {fpk.name:20} — {reason}")
            continue

        target_dir = out_root / subdir

        print(f"[extract] {fpk.name:20} → {target_dir}/  ({reason})")
        try:
            with fpk.open("rb") as fp:
                archive = FpkArchive(fp)
                archive.extract_to(target_dir)
        except Exception as e:
            print(f"  !! Failed: {e}")