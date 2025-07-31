import os
import time
import requests
import argparse
from Crypto.Cipher import AES
from concurrent import futures
from datetime import datetime, timezone
from tools import application_info_pb2, assetbundle_info_pb2
from google.protobuf.json_format import MessageToDict
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default=r"E:\Game_Dataset\jp.co.craftegg.band\RAW")
    parser.add_argument("--threads", default=32)
    return parser.parse_args()

APP_HASH = "e15bca7f8e1c11ad1284a3ac1f9863b3a513c921c6f8a57a8fbd153c7539055c"
APP_URL = "https://api.garupa.jp/api/application"
ASSET_URL = "https://content.garupa.jp/Release"

PROXIES= {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897",
}

USER_AGENT = "UnityPlayer/2021.3.39f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"

HEADERS1 = {
    "Host":             "api.garupa.jp",
    "User-Agent":       USER_AGENT,
    "Accept-Encoding":  "deflate, gzip",
    "Content-Type":     "application/octet-stream",
    "Accept":           "application/octet-stream",
    "X-ClientVersion":  "9.1.0",
    "X-Signature":      "3cde36c1-b431-4458-90cf-469cb0096e0a",
    "X-ClientPlatform": "Android",
}

HEADERS2 = {
    "Host":             "content.garupa.jp",
    "User-Agent":       USER_AGENT,
    "Accept-Encoding":  "deflate, gzip",
    "X-ClientPlatform": "Android",
    "X-Unity-Version":  "2021.3.39f1",
}

columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

def get_asset_url_dec(data):
    key = b"mikumikulukaluka"
    iv = b"lukalukamikumiku" 
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(data)
    pad_len = padded[-1]
    return padded[:-pad_len]

def get_asset_url():
    resp = requests.get(APP_URL, headers=HEADERS1, proxies=PROXIES)
    resp.raise_for_status()
    app_info = application_info_pb2.AppGetResponse()
    resp = get_asset_url_dec(resp.content)
    app_info.ParseFromString(resp)
    app_version = app_info.dataVersion

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    url_meta = f"{ASSET_URL}/{app_version}_{APP_HASH}/Android/AssetBundleInfo?t={timestamp}"
    url_ab = f"{ASSET_URL}/{app_version}_{APP_HASH}/Android"
    resp = requests.get(url_meta, headers=HEADERS2, proxies=PROXIES)
    resp.raise_for_status()

    info = assetbundle_info_pb2.AssetBundleInfo()
    info.ParseFromString(resp.content)
    bundle = MessageToDict(info)
    return bundle, url_ab

def handler_assetbundle_info(root, data):
    bundles = []
    total_filesize = 0
    filters = ["scenario", "story", "sound"]

    with Progress(*columns, transient=True) as progress:
        task_id = progress.add_task("Checking", total=None)
        for item in data["Bundles"].values():
            name = item["BundleName"] + ".unity3d"
            #if not any(name.startswith(f) for f in filters):
                #continue
            total_filesize += int(item["FileSize"])
            bundles.append(name)

            progress.update(task_id, advance=1)
        total_filesize = total_filesize / (1024 ** 3)
    return bundles, total_filesize

def worker(bundle_name, base_url, out_root):
    dest_path = os.path.join(out_root, bundle_name)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    session = requests.Session()
    session.proxies.update(PROXIES)
    session.headers.update({"User-Agent": USER_AGENT})

    while True:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        url = f"{base_url}/{bundle_name.replace(".unity3d", "")}?t={timestamp}"
        try:
            resp = session.get(url)
            resp.raise_for_status()
            with open(dest_path, 'wb') as f:
                f.write(resp.content)
                return
        except Exception as exc:
            print(f"[Warning] {bundle_name}")
            time.sleep(1)

if __name__ == "__main__":
    args = args_parser()
    bundle_info_dict, url_ab = get_asset_url()
    bundles, total_filesize = handler_assetbundle_info(args.output_dir, bundle_info_dict)

    print(f"Total payload: {total_filesize:.2f} GiB ({len(bundles):,} files)")

    os.makedirs(args.output_dir, exist_ok=True)

    with Progress(*columns) as progress:
        task_id = progress.add_task("Downloading", total=len(bundles))
        with futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            future_list = [executor.submit(worker, name, url_ab, args.output_dir) for name in bundles]
            for _ in futures.as_completed(future_list):
                progress.update(task_id, advance=1)