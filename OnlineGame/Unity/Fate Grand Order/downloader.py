import os
import json
import time
import hashlib
import requests
import argparse
import binascii
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

def parser_args():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=r"E:\Game_Dataset\com.aniplex.fategrandorder\RAW")
    p.add_argument("--workers", type=int, default=32)
    return p.parse_args()

columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

@dataclass
class AssetRow:
    rel_path: str  # 文件相对路径（Movie/ops00100.usm）
    size: int      # 字节大小
    crc32: int     # 十进制 CRC32

def category_of(path: str) -> str:
    bname = os.path.basename(path).lower()
    if bname.endswith(".cpk.bytes"):
        return "Audio"
    if bname.endswith(".usm"):
        return "Movie"
    return "Assetbundle"   # 无后缀视为 ab 包

def get_sha_name(name):
    sha1 = hashlib.sha1()
    sha1.update(name.encode("utf-8"))
    hashed = sha1.digest()
    return "".join(f"{b ^ 0xAA:02x}" for b in hashed) + ".bin"

def bytes_to_gib(n):
    return round(n / 1024 ** 3, 2)

def crc32_of_file(fp):
    with open(fp, "rb") as f:
        data = f.read()
    return binascii.crc32(data) & 0xFFFFFFFF

def local_dest_path(root, row):
    rel = row.rel_path
    if category_of(rel) == "Assetbundle" and os.path.splitext(os.path.basename(rel))[1] == "":
        rel += ".unity3d"
    return os.path.join(root, rel)

def read_version_info(root):
    storage_path = os.path.join(root, "3_AssetStorage.txt")
    with open(storage_path, "r", encoding="utf-8") as fp:
        lines = [ln.strip() for ln in fp if ln.strip()]

    ver_parts = lines[1].split(",")
    version_param = f"{ver_parts[0].lstrip('@')}_{ver_parts[1]}"
    return version_param, lines[2:]

def read_folder_name(root):
    bundle_path = os.path.join(root, "2_assetbundle.json")
    with open(bundle_path, "r", encoding="utf-8") as fp:
        obj = json.load(fp)
    return obj["folderName"].rstrip("/")

def parse_asset_rows(raw_lines):
    rows = []
    for ln in raw_lines:
        parts = ln.split(",")
        if len(parts) < 5:
            continue
        rows.append(AssetRow(rel_path=parts[4], size=int(parts[2]), crc32=int(parts[3])))
    return rows

def build_url(base_root, ver_param, row: AssetRow):
    cat = category_of(row.rel_path)
    if cat == "Assetbundle":
        server_name = get_sha_name(row.rel_path.replace('/', '@') + '.unity3d')
    else:
        server_name = row.rel_path.replace("/", "_")
    return f"{base_root}{server_name}?v={ver_param}_{row.size}_{row.crc32}"

def ensure_dir(path):
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

def download(sess, url, dest):
    while True:
        try:
            r = sess.get(url)
            r.raise_for_status()
            ensure_dir(dest)
            with open(dest, "wb") as fp:
                fp.write(r.content)
            return
        except Exception as e:
            print(f"[W] {os.path.basename(dest)} Download failed: ({e})")
            time.sleep(1)

def main():
    args = parser_args()
    root = args.root
    workers = args.workers

    version_param, asset_lines = read_version_info(root)
    folder_name = read_folder_name(root)
    base_root = f"https://cdn.data.fate-go.jp/AssetStorages/{folder_name}/Android/"

    rows = parse_asset_rows(asset_lines)

    size_map = {"Audio": 0, "Movie": 0, "Assetbundle": 0}
    for r in rows:
        size_map[category_of(r.rel_path)] += r.size

    print(
        f"Audio payload      : {bytes_to_gib(size_map['Audio']):>7.2f} GiB ({size_map['Audio']:,} bytes)\n"
        f"Movie payload      : {bytes_to_gib(size_map['Movie']):>7.2f} GiB ({size_map['Movie']:,} bytes)\n"
        f"AssetBundle payload: {bytes_to_gib(size_map['Assetbundle']):>7.2f} GiB ({size_map['Assetbundle']:,} bytes)\n"
        f"Total payload      : {bytes_to_gib(sum(size_map.values())):>7.2f} GiB ({sum(size_map.values()):,} bytes)\n"
    )

    need_download = []
    with Progress(*columns) as prog:
        crc_task = prog.add_task("Checking CRC", total=len(rows))
        for r in rows:
            local_path = local_dest_path(root, r)
            if os.path.isfile(local_path) and crc32_of_file(local_path) == r.crc32:
                pass
            else:
                need_download.append((r, local_path))
            prog.update(crc_task, advance=1)

    print(f"Need download: {len(need_download):,} / {len(rows):,}")

    if not need_download:
        print("All files are up-to-date.")
        return

    sess = requests.Session()
    sess.proxies.update({"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"})
    with Progress(*columns) as prog:
        task = prog.add_task("Downloading", total=len(need_download))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(download, sess, build_url(base_root, version_param, r), dest_path) for r, dest_path in need_download]
            for f in as_completed(futs):
                f.result()
                prog.update(task, advance=1)

if __name__ == "__main__":
    main()