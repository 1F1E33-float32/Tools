# https://github.com/YuriSizuku/GalgameReverse
from __future__ import annotations

import argparse
import mmap
import os
import struct
from typing import List


class struct_t(struct.Struct):
    _meta_fmt: str = ""
    _meta_names: List[str] = []

    def __init__(self, data: bytes | None = None, cur: int = 0, *, fmt: str | None = None, names: List[str] | None = None) -> None:
        if names is not None:
            self._meta_names = names
        if fmt is not None:
            self._meta_fmt = fmt
        super().__init__(self._meta_fmt)
        if data is not None:
            self.frombytes(data, cur)

    def cppinherit(self, fmt: str, names: List[str]) -> None:
        self._meta_names = names + self._meta_names
        self._meta_fmt = fmt.lstrip("<>") + self._meta_fmt.lstrip("<>")

    def frombytes(self, data: bytes, cur: int = 0, *, fmt: str | None = None) -> None:
        values = struct.unpack_from(fmt or self._meta_fmt, data, cur)
        for i, val in enumerate(values[: len(self._meta_names)]):
            setattr(self, self._meta_names[i], val)
        self._data = data  # keep a ref for debugging

    def tobytes(self, *, fmt: str | None = None) -> bytes:
        values = [getattr(self, name) for name in self._meta_names]
        return struct.pack(fmt or self._meta_fmt, *values)


class archeader_t(struct_t):
    def __init__(self, data: bytes | None = None, cur: int = 0):
        self.magic: bytes = b"MajiroArcV3.000\0"
        self.count: int = 0
        self.name_offset: int = 0
        self.data_offset: int = 0
        super().__init__(data, cur, fmt="<16s3I", names=["magic", "count", "name_offset", "data_offset"])


class arcentry_t(struct_t):
    def __init__(self, data: bytes | None = None, cur: int = 0, *, fmt: str | None = None, names: List[str] | None = None):
        self.hash: int = 0
        self.offset: int = 0
        self.length: int = 0
        self._addr = cur  # original address inside the file (debugging aid)
        super().__init__(data, cur, fmt=fmt, names=names)


class arcentryv3_t(arcentry_t):
    def __init__(self, data: bytes | None = None, cur: int = 0):
        self.cppinherit("<QII", ["hash", "offset", "length"])
        super().__init__(data, cur)

    @staticmethod
    def crc(data: bytes, init: int = 0) -> int:
        POLY = 0x42F0E1EBA9EA3693

        def _calc64(idx: int) -> int:
            v = idx
            for _ in range(8):
                v = (v >> 1) ^ POLY if v & 1 else v >> 1
            return v

        v = (~init) & 0xFFFFFFFFFFFFFFFF
        for b in data:
            v = (v >> 8) ^ _calc64((v ^ b) & 0xFF)
        return (~v) & 0xFFFFFFFFFFFFFFFF


class Arc:
    def __init__(self, data: bytes | None = None, encoding: str = "shift_jis") -> None:
        self.m_header = archeader_t()
        self.m_entries: List[arcentryv3_t] = []
        self.m_names: List[str] = []
        self._encoding = encoding
        if data is not None:
            self.parse(data)

    def parse(self, data: bytes) -> None:
        self.m_data = data  # memoryview / mmap for zero‑copy slices
        self.m_header = archeader_t(data)

        if self.m_header.magic != b"MajiroArcV3.000\0":
            raise ValueError(f"Unsupported format: {self.m_header.magic!r}")

        entry_size = arcentryv3_t().size  # 16 bytes
        toc_start = self.m_header.size
        for i in range(self.m_header.count):
            self.m_entries.append(arcentryv3_t(data, toc_start + i * entry_size))

        # Filenames are null‑terminated strings packed back‑to‑back.
        cur = self.m_header.name_offset
        for _ in range(self.m_header.count):
            end = data.find(b"\0", cur)
            if end == -1:
                raise ValueError("Corrupted archive: unterminated filename")
            filename = bytes(data[cur:end]).decode(self._encoding)
            self.m_names.append(filename)
            cur = end + 1

    def export(self, outdir: str) -> None:
        for idx, (name, entry) in enumerate(zip(self.m_names, self.m_entries), 1):
            dst_path = os.path.join(outdir, name)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            print(f"{idx}/{len(self.m_names)} » {name}  hash={entry.hash:016X}  offset={entry.offset:X}  length={entry.length:X}")

            with open(dst_path, "wb") as fp:
                slice_start = entry.offset
                slice_end = slice_start + entry.length
                fp.write(self.m_data[slice_start:slice_end])


def export_arc(arc_path: str, outdir: str = "out", *, encoding: str = "shift_jis") -> None:
    with open(arc_path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        arc = Arc(mm, encoding)
        arc.export(outdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default=r"E:\VN\_tmp\#JA\みずいろリメイク\voice.arc")
    parser.add_argument("--outdir", default=r"D:\Fuck_VN\voice")
    parser.add_argument("--encoding", default="cp932")
    args = parser.parse_args()

    export_arc(args.archive, args.outdir, encoding=args.encoding)
