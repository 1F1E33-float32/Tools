import time
import xxhash
import requests
import argparse
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)

BASE_RES_ROOT = "https://prd-priconne-redive.akamaized.net/dl/Resources/10063900/Jpn"

MANIFEST_ROOT = f"{BASE_RES_ROOT}/AssetBundles/Android"
MANIFEST_FILE = f"{MANIFEST_ROOT}/manifest/manifest_assetmanifest"

MANIFEST_SOUND = f"{BASE_RES_ROOT}/Sound/manifest/soundmanifest"
MANIFEST_MOVIE = f"{BASE_RES_ROOT}/Movie/SP/High/manifest/movie2manifest"

POOL_ROOT_ASSETBUNDLES = "https://prd-priconne-redive.akamaized.net/dl/pool/AssetBundles"
POOL_ROOT_SOUND =        "https://prd-priconne-redive.akamaized.net/dl/pool/Sound"
POOL_ROOT_MOVIE =        "https://prd-priconne-redive.akamaized.net/dl/pool/Movie"

columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

def parser_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\RAW"))
    parser.add_argument("--workers", type=int, default=16)
    return parser.parse_args()

@dataclass()
class AssetRow:
    rel_path: str   # column 0 – relative file path
    hash_: str      # column 2 – 64‑char hex string
    size: int       # column 4 – file size in bytes
    category: str   # "sound" | "movie" | "other"

def bytes_to_gib(n):
    return round(n / 1024 ** 3, 2)

def file_xxh64(path):
    return xxhash.xxh64(path.read_bytes()).hexdigest()

def create_session():
    sess = requests.Session()
    return sess

def fetch_text(sess, url):
    resp = sess.get(url)
    resp.raise_for_status()
    return resp.text

def parse_manifest_lines(lines):
    result = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split(",")
        if len(parts) < 5:
            continue
        size = int(parts[4]) if parts[4].isdigit() else 0
        result.append((parts[0], parts[1], parts[2], parts[3], size))
    return result

def pool_root_for(cat):
    return (POOL_ROOT_SOUND if cat == "sound" else POOL_ROOT_MOVIE if cat == "movie" else POOL_ROOT_ASSETBUNDLES)

def build_asset_url(hash_str, cat):
    root = pool_root_for(cat)
    return f"{root}/{hash_str[:2]}/{hash_str}"

def download_asset(sess, url, dest):
    while True:
        try:
            resp = sess.get(url)
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.content)
            return
        except Exception as exc:
            print(f"[W] Download failed: {exc}")
            time.sleep(1)

def gather_assets(sess):
    print("Fetching master manifest…")
    master_text = fetch_text(sess, MANIFEST_FILE)
    master_items = parse_manifest_lines(master_text.splitlines())

    extra_manifest_urls = [MANIFEST_SOUND]
    master_items.extend([(url, "", "", "", 0) for url in extra_manifest_urls])

    print(f"Found {len(master_items)} sub‑manifests, fetching…")
    assets = []

    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Fetching", total=len(master_items)) 
        for col0, *_ in master_items:
            if col0.startswith("http"):
                url = col0
                cat = "sound" if "soundmanifest" in url else "movie" if "movie" in url else "other"
            else:
                url = f"{MANIFEST_ROOT}/{col0}"
                cat = "other"

            sub_text = fetch_text(sess, url)
            for p0, _, p2, _, sz in parse_manifest_lines(sub_text.splitlines()):
                assets.append(AssetRow(p0, p2, sz, cat))
            prog.update(task_id, advance=1)

    return assets

def summarize_payload(assets):
    total_sound = sum(a.size for a in assets if a.category == "sound")
    total_movie = sum(a.size for a in assets if a.category == "movie")
    total_other = sum(a.size for a in assets if a.category == "other")

    print(
        f"Sound payload : {bytes_to_gib(total_sound):.2f} GiB ({total_sound:,} bytes)\n"
        f"Movie payload : {bytes_to_gib(total_movie):.2f} GiB ({total_movie:,} bytes)\n"
        f"Other payload : {bytes_to_gib(total_other):.2f} GiB ({total_other:,} bytes)\n"
        )

def filter_existing(assets, root):
    to_dl = []
    skipped = 0

    print("Scanning existing files (XXH64)…")
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Scanning", total=len(assets)) 
        for a in assets:
            dest = root / a.rel_path
            if dest.is_file():
                if file_xxh64(dest) == a.hash_:
                    skipped += 1
                    continue
            to_dl.append(a)
            prog.update(task_id, advance=1)
    return to_dl, skipped

def download_many(assets, root, sess, workers):
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Downloading", total=len(assets))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(download_asset, sess, build_asset_url(a.hash_, a.category), root / a.rel_path) for a in assets]
            for fut in as_completed(futures):
                fut.result()
                prog.update(task_id, advance=1)

def main(out_root, workers):
    out_root.mkdir(parents=True, exist_ok=True)
    sess = create_session()

    assets = gather_assets(sess)
    summarize_payload(assets)

    to_dl, skipped = filter_existing(assets, out_root)
    print(f"Start downloading assets… (total: {len(to_dl)}, skipped: {skipped})\n")

    if not to_dl:
        print("Up to date")
        return

    download_many(to_dl, out_root, sess, workers)
    print("Success")

if __name__ == "__main__":
    args = parser_args()
    main(args.root, args.workers)