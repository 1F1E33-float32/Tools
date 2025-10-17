import argparse
import multiprocessing
import os
import struct
import zlib
from compression.zstd import ZstdDecompressor
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
from huffman_decoder import HuffmanDecoder
from tqdm import tqdm


@dataclass
class PackageEntry:
    name: str
    position: int
    original_size: int
    compressed_size: int

    @staticmethod
    def from_bytes(data: bytes, codepage: str = "gbk") -> "PackageEntry":
        name = data[:0x40].rstrip(b"\x00").decode(codepage, errors="ignore")
        position, original_size, compressed_size = struct.unpack("<III", data[0x40:0x4C])
        return PackageEntry(name, position, original_size, compressed_size)


class PackageUnpacker:
    def __init__(self, pac_path: str, codepage: str = "gbk"):
        self.pac_path = pac_path
        self.codepage = codepage
        self.entry_count = 0
        self.compression_method = 0
        self.entries: List[PackageEntry] = []

    def _read_header(self, fp) -> bool:
        magic = fp.read(4)
        if magic[:3] != b"PAC":
            print("ERROR: Invalid package file (wrong magic).")
            return False

        self.entry_count = struct.unpack("<I", fp.read(4))[0]
        self.compression_method = struct.unpack("<I", fp.read(4))[0]

        print(f"Total {self.entry_count} files in the package.")
        print(f"Compression method: {self.compression_method}")

    def _read_index(self, fp) -> bool:
        fp.seek(-4, os.SEEK_END)
        compressed_index_size = struct.unpack("<I", fp.read(4))[0]

        fp.seek(-(compressed_index_size + 4), os.SEEK_END)
        compressed_index = ~np.frombuffer(fp.read(compressed_index_size), dtype=np.uint8) & 0xFF

        index_size = 0x4C * self.entry_count
        index_data = HuffmanDecoder(compressed_index.tobytes()).decode(index_size)

        self.entries = [PackageEntry.from_bytes(index_data[i * 0x4C : (i + 1) * 0x4C], self.codepage) for i in range(self.entry_count)]

    def _decompress_data(self, compressed_data: bytes, original_size: int, compressed_size: int) -> Optional[bytes]:
        if original_size == compressed_size:
            return compressed_data

        if self.compression_method == 4:
            return zlib.decompress(compressed_data)
        elif self.compression_method == 7:
            return ZstdDecompressor().decompress(compressed_data)

    def _extract_single_file(self, entry: PackageEntry, fp, output_dir: Path, pbar: Optional[tqdm] = None):
        fp.seek(entry.position, os.SEEK_SET)

        if self.compression_method != 0:
            compressed_data = fp.read(entry.compressed_size)
            uncompressed_data = self._decompress_data(compressed_data, entry.original_size, entry.compressed_size)
            if uncompressed_data is None:
                pbar.update(1)
                return
        else:
            uncompressed_data = fp.read(entry.compressed_size)

        output_path = output_dir / entry.name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(uncompressed_data)

        pbar.update(1)

    def extract(self, output_dir: str, threads: int = 0) -> bool:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with open(self.pac_path, "rb") as fp:
            self._read_header(fp)
            self._read_index(fp)

        if threads <= 0:
            threads = multiprocessing.cpu_count()

        with tqdm(total=self.entry_count, ncols=150) as pbar:
            if threads == 1:
                with open(self.pac_path, "rb") as fp:
                    for entry in self.entries:
                        self._extract_single_file(entry, fp, output_path, pbar)
            else:
                files_per_thread = (self.entry_count + threads - 1) // threads
                tasks = [self.entries[i * files_per_thread : min((i + 1) * files_per_thread, self.entry_count)] for i in range(threads) if i * files_per_thread < self.entry_count]

                with ThreadPoolExecutor(max_workers=threads) as executor:

                    def worker(entries):
                        with open(self.pac_path, "rb") as fp:
                            for entry in entries:
                                self._extract_single_file(entry, fp, output_path, pbar)

                    futures = [executor.submit(worker, chunk) for chunk in tasks]
                    for future in as_completed(futures):
                        future.result()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pac_file", help="Package file path")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--codepage", default="utf-8")
    parser.add_argument("--threads", type=int, default=0)

    args = parser.parse_args()

    unpacker = PackageUnpacker(args.pac_file, args.codepage)
    unpacker.extract(args.output_dir, threads=args.threads)
