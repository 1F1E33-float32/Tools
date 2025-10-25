import argparse
import glob
import os
from pathlib import Path

import xxhash
from MX_crypto import Mt19937, next_bytes


def decrypt_file(src_path: Path, dst_root: Path, in_root: Path, type_map):
    rel_path = src_path.relative_to(in_root)
    out_path = dst_root / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = src_path.read_bytes()
    name = src_path.stem
    type_name = type_map.get(name.lower(), name)
    seed = xxhash.xxh32(type_name.encode("utf-8"), seed=0).intdigest() & 0xFFFFFFFF
    rng = Mt19937(seed)
    ks = next_bytes(rng, len(data))
    dec = bytes(b ^ k for b, k in zip(data, ks))
    out_path.write_bytes(dec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", help="输入包含 .bytes 的目录（递归）")
    ap.add_argument("output_dir", help="输出目录")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)

    if not in_dir.is_dir():
        raise SystemExit(f"输入目录无效: {in_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    base_dir = Path(__file__).parent
    type_names = set()

    global_dir = base_dir / "Global"
    if global_dir.is_dir():
        for f in global_dir.rglob("*.py"):
            type_names.add(f.stem)

    type_map = {n.lower(): n for n in type_names}

    pattern = str(in_dir / "**" / "*.bytes")
    paths = [Path(p) for p in glob.glob(pattern, recursive=True) if os.path.isfile(p)]
    if not paths:
        print("未发现 .bytes 文件")
        return

    for p in paths:
        try:
            decrypt_file(p, out_dir, in_dir, type_map)
            print(f"已解密: {p.relative_to(in_dir)}")
        except Exception as e:
            print(f"解密失败: {p.relative_to(in_dir)}: {e}")


if __name__ == "__main__":
    main()
