import argparse
import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import repeat

import requests
from requests.adapters import HTTPAdapter
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from urllib3.util.retry import Retry

columns = (
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(bar_width=100),
    "[progress.percentage]{task.percentage:>6.2f}%",
    TextColumn("{task.completed}/{task.total}"),
    TimeElapsedColumn(),
    "•",
    TimeRemainingColumn(),
)

RESOURCE_TYPE_MAP = {
    "story": "Windows/assetbundles",
    "sound": "Generic",
    "home": "Generic",
    "race": "Generic",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/RAW")
    parser.add_argument("--meta", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/RAW/meta")
    parser.add_argument("--thread", type=int, default=32)
    return parser.parse_args()


class Game_API:
    def __init__(self):
        self.ASSET_URL = "https://prd-storage-app-umamusume.akamaized.net/dl/resources/"

        self.session = requests.Session()
        retries = Retry(total=100, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retries)
        self.session.mount("https://", adapter)

    def _post(self, url, data=None, extra_headers=None, **kw):
        hdr = self.session.headers.copy()
        if extra_headers:
            hdr.update(extra_headers)
        return self.session.post(url, data=data, headers=hdr, **kw)

    def _get(self, url, extra_headers=None, **kw):
        hdr = self.session.headers.copy()
        if extra_headers:
            hdr.update(extra_headers)
        return self.session.get(url, headers=hdr, **kw)

    def call_asset(self, endpoint):
        url = self.ASSET_URL + endpoint
        while True:
            try:
                resp = self._get(url)
                resp.raise_for_status()
                return resp.content
            except requests.RequestException as e:
                print(f"[W] {e}")
                time.sleep(2)


def load_manifest(meta_path):
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Meta database not found: {meta_path}")

    conn = sqlite3.connect(meta_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT n, h, m, l FROM a")
        rows = cursor.fetchall()
    finally:
        conn.close()
    return rows


def _prepare_task(row, raw_root):
    original_name = row["n"]
    hash_name = row["h"]
    asset_type_key = row["m"]
    raw_size = row["l"]

    if not original_name or not hash_name:
        return None

    if asset_type_key not in RESOURCE_TYPE_MAP:
        return None
    resource_type = RESOURCE_TYPE_MAP[asset_type_key]

    prefix = hash_name[:2]
    endpoint = f"{resource_type}/{prefix}/{hash_name}"

    normalized_name = original_name.replace("\\", "/")
    parts = [segment for segment in normalized_name.split("/") if segment]
    dest_path = os.path.join(raw_root, *parts)

    expected_size = None
    if raw_size is not None:
        try:
            expected_size = int(raw_size)
        except (TypeError, ValueError):
            expected_size = None

    if expected_size is not None and os.path.exists(dest_path):
        try:
            if os.path.getsize(dest_path) == expected_size:
                return None
        except OSError:
            pass

    return endpoint, dest_path


def build_download_tasks(rows, raw_root, workers=None):
    tasks = []
    total_rows = len(rows)
    if total_rows == 0:
        return tasks

    if workers is None or workers <= 0:
        workers = os.cpu_count() or 1
    workers = max(1, min(workers, total_rows))

    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Scanning", total=total_rows)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(_prepare_task, rows, repeat(raw_root)):
                if result:
                    tasks.append(result)
                prog.update(task_id, advance=1)
    return tasks


def download_assets(api, tasks, workers):
    if not tasks:
        print("[I] No assets to download.")
        return

    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Downloading", total=len(tasks))
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            future_to_info = {pool.submit(api.call_asset, endpoint): (endpoint, dest) for endpoint, dest in tasks}
            for future in as_completed(future_to_info):
                endpoint, dest = future_to_info[future]
                try:
                    content = future.result()
                    dest_dir = os.path.dirname(dest)
                    if dest_dir:
                        os.makedirs(dest_dir, exist_ok=True)
                    with open(dest, "wb") as fp:
                        fp.write(content)
                except Exception as exc:
                    prog.console.log(f"[E] Failed downloading {endpoint} -> {dest}: {exc}")
                finally:
                    prog.update(task_id, advance=1)


if __name__ == "__main__":
    args = parse_args()
    manifest_rows = load_manifest(args.meta)
    download_tasks = build_download_tasks(manifest_rows, args.RAW, args.thread)

    api = Game_API()
    download_assets(api, download_tasks, args.thread)
