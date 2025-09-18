import argparse
import io
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator, List, Optional

HDR_SIZE = 56
MAGIC = b"FPD\x00"


def read_cstr(buf: io.BytesIO) -> bytes:
    out = bytearray()
    while True:
        ch = buf.read(1)
        if not ch or ch == b"\x00":
            break
        out.extend(ch)
    return bytes(out)


def xor_inplace(buf: bytearray, key: bytes) -> None:
    if not key:
        return
    klen = len(key)
    # Use memoryview for speed; tight Python loop is still ok here.
    mv = memoryview(buf)
    for i in range(len(mv)):
        mv[i] ^= key[i % klen]


@dataclass
class EntryHdr:
    filepath_str_offset: int
    offset: int
    size: int
    uncompressed_size: int
    filepath: Optional[str] = None

    @classmethod
    def parse_from(cls, cur: io.BytesIO) -> "EntryHdr":
        # Entry is 4x u64 big-endian
        try:
            fso, off, size, usize = struct.unpack(">QQQQ", cur.read(8 * 4))
        except struct.error as e:
            raise ValueError(f"Truncated entry header: {e}") from e
        return cls(fso, off, size, usize)

    def __str__(self) -> str:
        return f"filepath: {self.filepath}\noffset: 0x{self.offset:X}\nsize: 0x{self.size:X}\nuncompressed_size: 0x{self.uncompressed_size:X}\n"


class FPD:
    def __init__(self, file: Path | str, key: bytes):
        self.filepath = Path(file)
        self.fpd_file = self.filepath.name
        self.key = key
        self.entries: List[EntryHdr] = []
        self.version: int = 0
        self.entry_count: int = 0
        self.entry_block_size: int = 0  # bytes (excludes HDR_SIZE)
        self.zlib_block_offset: int = 0
        self.zlib_block_size: int = 0
        self._parse()

    # ---- Parsing helpers ----
    def _parse(self) -> None:
        with self.filepath.open("rb") as f:
            cur = io.BytesIO(f.read(HDR_SIZE))
            magic = cur.read(4)
            if magic != MAGIC:
                raise ValueError(f"Bad magic: expected {MAGIC!r}, found {magic!r} in {self.filepath}")
            self.version = int.from_bytes(cur.read(4), "big")
            self.entry_count = int.from_bytes(cur.read(8), "big")
            # entry_block_size as stored includes HDR_SIZE; subtract to get pure block length
            self.entry_block_size = int.from_bytes(cur.read(8), "big") - HDR_SIZE
            # skip 4 * u64 reserved
            cur.seek(4 * 8, io.SEEK_CUR)

            if self.entry_count < 0:
                raise ValueError("Negative entry count")
            if self.entry_block_size < 0:
                raise ValueError("Negative entry block size")

            # Now read the entry block only (not the whole file)
            f.seek(HDR_SIZE)
            raw_buf = bytearray(f.read(self.entry_block_size))
            if len(raw_buf) != self.entry_block_size:
                raise ValueError("Truncated entry block")

            # XOR-decrypt the entry block
            xor_inplace(raw_buf, self.key)

            # Parse entries
            entry_block_cur = io.BytesIO(raw_buf)

            # Each entry is 32 bytes
            expected_min = self.entry_count * 32
            if expected_min > self.entry_block_size:
                raise ValueError(f"Entry block too small: have {self.entry_block_size} for {self.entry_count} entries (need at least {expected_min})")

            self.entries = [EntryHdr.parse_from(entry_block_cur) for _ in range(self.entry_count)]

            # The remainder is a zlib-compressed string table
            self.zlib_block_offset = entry_block_cur.tell()
            self.zlib_block_size = self.entry_block_size - self.zlib_block_offset
            try:
                string_block = zlib.decompress(entry_block_cur.read(self.zlib_block_size))
            except zlib.error as e:
                raise ValueError(f"Failed to decompress string table: {e}") from e

            # Assign filepaths via offsets
            str_cur = io.BytesIO(string_block)
            for e in self.entries:
                if e.filepath_str_offset >= len(string_block):
                    raise ValueError(f"String offset {e.filepath_str_offset} out of bounds ({len(string_block)})")
                str_cur.seek(e.filepath_str_offset)
                try:
                    e.filepath = read_cstr(str_cur).decode("utf-8")
                except UnicodeDecodeError as ue:
                    raise ValueError(f"Invalid UTF-8 in path at offset {e.filepath_str_offset}") from ue

    def dump(self, out_root: Path | str) -> None:
        out_root = Path(out_root)
        out_root.mkdir(parents=True, exist_ok=True)

        with self.filepath.open("rb", buffering=0) as f:
            for idx, e in enumerate(self.entries):
                # Compute absolute data start: after header+entry_block
                data_start = HDR_SIZE + self.entry_block_size + e.offset
                f.seek(data_start)

                # Write either raw-xored or decompressed data
                out_path = out_root / e.filepath
                out_path.parent.mkdir(parents=True, exist_ok=True)

                # Stream to avoid large peak memory
                if e.uncompressed_size == 0:
                    # Not compressed: XOR and stream out
                    with out_path.open("wb") as fout:
                        for chunk in self._iter_xored_chunks(f, e.size):
                            fout.write(chunk)
                else:
                    # Compressed: XOR -> zlib.decompressobj stream -> write
                    dco = zlib.decompressobj()
                    with out_path.open("wb") as fout:
                        remaining = e.size
                        while remaining > 0:
                            to_read = min(1 << 20, remaining)  # 1 MiB chunks
                            buf = bytearray(f.read(to_read))
                            if not buf:
                                raise ValueError(f"Unexpected EOF reading entry at offset 0x{e.offset:X}")
                            remaining -= len(buf)
                            xor_inplace(buf, self.key)
                            try:
                                out = dco.decompress(buf)
                            except zlib.error as ze:
                                raise ValueError(f"zlib error while decompressing entry at offset 0x{e.offset:X}: {ze}") from ze
                            if out:
                                fout.write(out)
                        # flush remaining
                        tail = dco.flush()
                        if tail:
                            fout.write(tail)

    def _iter_xored_chunks(self, f: BinaryIO, total: int, chunk_size: int = 1 << 20) -> Iterator[bytes]:
        remaining = total
        while remaining > 0:
            to_read = min(chunk_size, remaining)
            buf = bytearray(f.read(to_read))
            if not buf:
                raise ValueError("Unexpected EOF in uncompressed entry data")
            xor_inplace(buf, self.key)
            remaining -= len(buf)
            yield bytes(buf)

    # Pretty print
    def describe(self) -> str:
        lines = [f"version: 0x{self.version:X}", f"file_count: 0x{self.entry_count:X}", f"hdr_entry_size: 0x{self.entry_block_size:X}"]
        for i, e in enumerate(self.entries):
            lines.append(f"\nNo.: {i}\n{e}")
        return "\n".join(lines)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=r"D:\Muv-Luv Tactics\pldep.dat")
    p.add_argument("--key_bin", default=r"D:\Project\Tools\VisualNovel\Engine\FSNr\decryptKey.bin")
    p.add_argument("--output_dir", default=r"D:\Muv-Luv Tactics\EX_pldep")
    p.add_argument("--single_file", default=True)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    key_path = Path(args.key_bin)
    input_path = Path(args.input)
    out_dir = Path(args.output_dir)

    key = key_path.read_bytes()
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    if args.single_file:
        # 单文件模式
        if not input_path.is_file():
            print(f"错误: {input_path} 不是一个文件")
        else:
            try:
                fpd = FPD(input_path, key)
                fpd.dump(out_dir)
                print(f"[OK] {input_path}  ->  {out_dir}")
                count += 1
            except Exception as e:
                print(f"[FAIL] {input_path}: {e}")
    else:
        # 文件夹模式
        if not input_path.is_dir():
            print(f"错误: {input_path} 不是一个文件夹")
        else:
            bin_iter = input_path.glob("*.bin")
            for bin_path in bin_iter:
                try:
                    fpd = FPD(bin_path, key)
                    fpd.dump(out_dir)
                    print(f"[OK] {bin_path}  ->  {out_dir}")
                    count += 1
                except Exception as e:
                    print(f"[FAIL] {bin_path}: {e}")

    if count == 0:
        print("未找到任何可处理的 .bin 文件。")
    else:
        print(f"完成：共处理 {count} 个 .bin 文件。")