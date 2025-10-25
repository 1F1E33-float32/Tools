import argparse
import os
import shutil
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from MX_crypto import derive_password

CHUNK_SIZE = 8 * 1024 * 1024
WRITE_BUFFERING = 8 * 1024 * 1024


def try_extract(zip_path: Path, out_dir: Path, password: bytes):
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.setpassword(password)
        for info in zf.infolist():
            name = info.filename
            target = (out_dir / name).resolve()
            if info.is_dir() or name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb", buffering=WRITE_BUFFERING) as dst:
                shutil.copyfileobj(src, dst, length=CHUNK_SIZE)
    return True, ""


def extract_single_zip(zip_path_str: str, out_root_str: str):
    zip_path = Path(zip_path_str)
    out_root = Path(out_root_str)
    filename = zip_path.name
    out_dir = out_root / zip_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    pw_candidates = [derive_password(filename.lower()), derive_password(filename)]

    last_err = ""
    for pw in pw_candidates:
        try:
            success, msg = try_extract(zip_path, out_dir, pw)
            if success:
                return (zip_path.name, True, "")
        except Exception as e:
            last_err = f"{e}"
            continue

    return (zip_path.name, False, last_err)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", help="输入文件夹")
    ap.add_argument("output_dir", help="输出文件夹")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    if not in_dir.is_dir():
        print(f"输入目录无效: {in_dir}", file=sys.stderr)
        sys.exit(2)
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_paths = [str(p) for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() == ".zip"]
    if not zip_paths:
        print("未发现 zip 文件")
        return

    max_workers = max(1, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(extract_single_zip, zp, str(out_dir)) for zp in zip_paths]
        for fu in as_completed(futures):
            name, success, msg = fu.result()
            if success:
                print(f"已解压: {name}")
            else:
                print(f"解压失败: {name}: {msg}", file=sys.stderr)


if __name__ == "__main__":
    main()
