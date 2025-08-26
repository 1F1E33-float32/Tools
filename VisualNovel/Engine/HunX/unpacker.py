import sys
import struct
import os
from pathlib import Path

MAGIC = b"HUNEXGGEFA10"

def extract_hfa(hfa_path: Path, out_root: Path) -> None:
    out_dir = out_root / hfa_path.stem
    os.makedirs(out_dir, exist_ok=True)

    with hfa_path.open("rb") as f:
        if f.read(12) != MAGIC:
            print(f"[跳过] {hfa_path.name}: 非法文件头")
            return

        (total_file_entries,) = struct.unpack("<I", f.read(4))
        entries = []
        entry_struct = struct.Struct("<96sII24x")  # name(96), offset(uint32), size(uint32), pad(24)

        for _ in range(total_file_entries):
            file_entry_name, file_entry_offset, file_entry_size = entry_struct.unpack(f.read(entry_struct.size))
            name_bytes = file_entry_name.rstrip(b"\x00")
            try:
                name_str = name_bytes.decode("ASCII")
            except UnicodeDecodeError:
                name_str = name_bytes.decode("ASCII", errors="replace")
            entries.append((name_str, file_entry_offset, file_entry_size))

        data_start = f.tell()

        entries.sort(key=lambda x: x[0])

        for name_str, offset, size in entries:
            f.seek(data_start + offset)
            data = f.read(size)

            safe_rel = os.path.normpath(name_str).lstrip("/\\")
            dest_path = out_dir / safe_rel
            os.makedirs(dest_path.parent, exist_ok=True)

            with dest_path.open("wb") as wf:
                wf.write(data)

    print(f"[完成] {hfa_path.name}  ->  {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python extract_hfa_bulk.py <输入文件夹> [输出文件夹]")
        sys.exit(1)

    in_dir = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        out_root = Path(sys.argv[2])
    else:
        out_root = Path(str(in_dir) + "_EX")

    os.makedirs(out_root, exist_ok=True)

    hfa_files = sorted([*in_dir.glob("*.hfa"), *in_dir.glob("*.HFA")])

    if not hfa_files:
        print(f"未在目录中找到 .hfa 文件: {in_dir}")
        sys.exit(0)

    for hfa in hfa_files:
        extract_hfa(hfa, out_root)