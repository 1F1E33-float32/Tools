import argparse
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, List

from tqdm import tqdm

# FPAC 文件头：
# magic:    4s    固定为 b'FPAC'
# count:    I     条目数量
# hdr_size: I     头部大小（包含目录等，具体视格式而定）
# unk:      I     未知/保留字段
HEADER_STRUCT = struct.Struct("<4sIII")

# 目录条目（每项 32 字节）：
# hash:        Q  8 字节（可能是哈希/ID）
# name_offset: Q  8 字节（文件名在文件中的偏移，指向以0结尾的字符串）
# size:        Q  8 字节（文件数据长度）
# location:    Q  8 字节（文件数据在文件中的偏移）
ENTRY_STRUCT = struct.Struct("<QQQQ")


@dataclass
class FpacHeader:
    magic: bytes
    count: int
    header_size: int
    unk: int


@dataclass
class FpacEntry:
    hash: int
    name_offset: int
    size: int
    location: int


def read_cstring(f: BinaryIO, offset: int, encoding: str = "utf-8") -> str:
    cur = f.tell()
    try:
        f.seek(offset)
        chunks = []
        while True:
            b = f.read(256)
            if not b:
                break
            i = b.find(b"\x00")
            if i != -1:
                chunks.append(b[:i])
                break
            chunks.append(b)
        return b"".join(chunks).decode(encoding, errors="replace")
    finally:
        f.seek(cur)


def parse_header(f: BinaryIO) -> FpacHeader:
    raw = f.read(HEADER_STRUCT.size)
    if len(raw) != HEADER_STRUCT.size:
        raise ValueError("文件过短，无法读取 FPAC 头。")
    magic, count, hdr_size, unk = HEADER_STRUCT.unpack(raw)
    if magic != b"FPAC":
        raise ValueError(f"魔数不匹配：期望 b'FPAC'，实际 {magic!r}")
    return FpacHeader(magic=magic, count=count, header_size=hdr_size, unk=unk)


def parse_entries(f: BinaryIO, count: int) -> List[FpacEntry]:
    entries: List[FpacEntry] = []
    for _ in range(count):
        raw = f.read(ENTRY_STRUCT.size)
        if len(raw) != ENTRY_STRUCT.size:
            raise ValueError("目录区不完整，无法读取条目。")
        h, name_off, size, loc = ENTRY_STRUCT.unpack(raw)
        entries.append(FpacEntry(hash=h, name_offset=name_off, size=size, location=loc))
    return entries


def extract_one(f: BinaryIO, entry: FpacEntry, out_base: Path) -> str:
    name = read_cstring(f, entry.name_offset)
    f.seek(entry.location)
    data = f.read(entry.size)
    if len(data) != entry.size:
        raise ValueError(f"读取数据不足：{name} 期望 {entry.size} 字节。")

    out_path = (out_base / name).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return name


def process_pac(pac_path: Path, out_dir: Path | None) -> None:
    out_base = (out_dir if out_dir is not None else pac_path.parent).resolve()

    with pac_path.open("rb") as f:
        header = parse_header(f)
        entries = parse_entries(f, header.count)

        with tqdm(total=header.count, unit="file", leave=True, ncols=150) as bar:
            for e in entries:
                try:
                    name = extract_one(f, e, out_base)
                    bar.set_postfix_str(name[:40], refresh=False)
                except Exception as ex:
                    tqdm.write(f"[{pac_path.name}] 提取失败: {ex}")
                finally:
                    bar.update(1)


def collect_pacs(input_path: Path | None) -> Iterable[Path]:
    if input_path is None:
        yield from Path(".").glob("*.pac")
        return

    p = input_path.resolve()
    if p.is_file():
        if p.suffix.lower() == ".pac":
            yield p
    elif p.is_dir():
        yield from p.rglob("*.pac")


def main() -> None:
    parser = argparse.ArgumentParser(description="FPAC 解包工具：支持文件或文件夹输入，进度用 tqdm 显示。")
    parser.add_argument(
        "input",
        nargs="?",
        help="单个 .pac 文件或一个文件夹（将递归扫描其中所有 .pac）。若不提供，则使用当前目录下的 *.pac。",
    )
    parser.add_argument(
        "-o",
        "--out",
        default=None,
        help="输出目录。不指定时，默认解压到各自 .pac 所在的文件夹。",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve() if args.input else None
    out_dir = Path(args.out).resolve() if args.out else None

    pac_files = list(collect_pacs(input_path))
    if not pac_files:
        print("未找到任何 .pac 文件。")
        return

    for pac in pac_files:
        if not pac.exists():
            print(f"跳过：{pac} 不存在。")
            continue
        process_pac(pac, out_dir)


if __name__ == "__main__":
    main()
