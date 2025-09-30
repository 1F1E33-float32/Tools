import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-in_dir", type=str, default=r"E:\VN\ja\Escude\Yuukoku no Femme Fatale")
    parser.add_argument("-out_dir", type=str, default=r"E:\VN\ja\Escude\Yuukoku no Femme Fatale\unpacked")
    return parser.parse_args(args=args, namespace=namespace)


MASK32 = 0xFFFFFFFF


def u32(x: int) -> int:
    return x & MASK32


def le_u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def le_i32(data: bytes, off: int) -> int:
    return struct.unpack_from("<i", data, off)[0]


@dataclass
class ArchiveEntry:
    name: str
    offset: int
    size: int


class IndexReader:
    def __init__(self, file_bytes: bytes):
        self._f = file_bytes
        self._len = len(file_bytes)
        self._seed = le_u32(self._f, 0x8)
        self.count = u32(le_u32(self._f, 0xC) ^ self._next_key())

    def _next_key(self) -> int:
        s = u32(self._seed ^ 0x65AC9365)
        s = u32(s ^ u32(((s >> 1) ^ s) >> 3) ^ u32(((u32(s << 1) ^ s) << 3)))
        self._seed = s
        return s

    def _decrypt_inplace(self, data: bytearray) -> None:
        off = 0
        for _ in range(len(data) // 4):
            v = struct.unpack_from("<I", data, off)[0] ^ self._next_key()
            struct.pack_into("<I", data, off, u32(v))
            off += 4

    def _get_cstring(self, blob: bytes, start: int, max_len: Optional[int]) -> str:
        end = len(blob) if max_len is None else min(len(blob), start + max_len)
        s = blob[start:end]
        z = s.find(b"\x00")
        if z != -1:
            s = s[:z]
        return s.decode("utf-8", errors="replace")

    def read_index_v1(self) -> List[ArchiveEntry]:
        idx_size = self.count * 0x88
        raw = bytearray(self._f[0x10 : 0x10 + idx_size])
        if len(raw) != idx_size:
            raise Exception("bad index v1")
        self._decrypt_inplace(raw)
        dir_, off, max_off = [], 0, self._len
        for _ in range(self.count):
            name = self._get_cstring(raw, off, 0x80)
            off0, size = le_u32(raw, off + 0x80), le_u32(raw, off + 0x84)
            if off0 + size > max_off:
                raise Exception("placement v1")
            dir_.append(ArchiveEntry(name, off0, size))
            off += 0x88
        return dir_

    def read_index_v2(self) -> List[ArchiveEntry]:
        names_size = u32(le_u32(self._f, 0x10) ^ self._next_key())
        index_size = self.count * 12
        idx_beg, names_beg = 0x14, 0x14 + index_size
        index_block = bytearray(self._f[idx_beg:names_beg])
        names_block = self._f[names_beg : names_beg + names_size]
        if len(index_block) != index_size or len(names_block) != names_size:
            raise Exception("bad index v2")
        self._decrypt_inplace(index_block)
        dir_, off, max_off = [], 0, self._len
        for _ in range(self.count):
            noff = le_i32(index_block, off)
            if noff < 0 or noff >= len(names_block):
                raise Exception("name off v2")
            name = self._get_cstring(names_block, noff, None)
            off0, size = le_u32(index_block, off + 4), le_u32(index_block, off + 8)
            if off0 + size > max_off:
                raise Exception("placement v2")
            dir_.append(ArchiveEntry(name, off0, size))
            off += 12
        return dir_


def open_escude_archive(path_or_bytes) -> List[ArchiveEntry]:
    data = bytes(path_or_bytes) if isinstance(path_or_bytes, (bytes, bytearray)) else Path(path_or_bytes).read_bytes()
    if len(data) < 0x14:
        raise Exception("too small")
    if data[0:4] != b"ESC-":
        raise Exception("sig")
    if data[4:7] != b"ARC":
        raise Exception("magic")
    version = data[7] - ord("0")
    r = IndexReader(data)
    if version == 1:
        return r.read_index_v1()
    if version == 2:
        return r.read_index_v2()
    raise Exception(f"version {version}")


def extract_pack(pack_path: Path, out_root: Path) -> int:
    pack_name = pack_path.stem
    dest_dir = out_root / pack_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    data = pack_path.read_bytes()
    entries = open_escude_archive(data)
    n = 0
    for e in entries:
        rel = Path(e.name.replace("\\", "/"))
        out_path = dest_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data[e.offset : e.offset + e.size])
        n += 1
    return n


def main(argv=None):
    args = parse_args(argv)
    in_dir = Path(args.in_dir) if args.in_dir else None
    if not in_dir or not in_dir.is_dir():
        print("ERR: -in_dir invalid")
        sys.exit(2)
    out_dir = Path(args.out_dir) if args.out_dir else (in_dir / "unpacked")
    out_dir.mkdir(parents=True, exist_ok=True)

    packs = [p for p in (in_dir / "data.bin", in_dir / "script.bin") if p.is_file()]
    if not packs:
        print("No data.bin/script.bin found.")
        return

    total = 0
    for p in packs:
        try:
            print(f"[+] {p.name}")
            total += extract_pack(p, out_dir)
        except Exception as ex:
            print(f"[!] fail {p}: {ex}")
    print(f"Done. files: {total}")


if __name__ == "__main__":
    main()
