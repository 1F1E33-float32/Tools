import argparse
import glob
import json
import os
from pathlib import Path
from fbs_parser import deserialize_bytes_file


def parse_file(src_path: Path, dst_root: Path, in_root: Path):
    rel_path = src_path.relative_to(in_root)
    out_path = (dst_root / rel_path).with_suffix(".json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = deserialize_bytes_file(src_path)
    if not records:
        return False
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", help="输入包含 .bytes 的目录（递归）")
    ap.add_argument("output_dir", help="输出目录（保存为 .json）")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    if not in_dir.is_dir():
        raise SystemExit(f"输入目录无效: {in_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    pattern = str(in_dir / "**" / "*.bytes")
    paths = [Path(p) for p in glob.glob(pattern, recursive=True) if os.path.isfile(p)]
    if not paths:
        print("未发现 .bytes 文件")
        return

    for p in paths:
        try:
            ok = parse_file(p, out_dir, in_dir)
            if ok:
                print(f"已解析: {p.relative_to(in_dir)}")
            else:
                print(f"跳过（未找到 schema 或空数据）: {p.relative_to(in_dir)}")
        except Exception as e:
            print(f"解析失败: {p.relative_to(in_dir)}: {e}")


if __name__ == "__main__":
    main()
