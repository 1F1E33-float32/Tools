import os
import time
import hashlib
import requests
import argparse
from tools import octo_pb2
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from google.protobuf.json_format import MessageToDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)
columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"E:\Game_Dataset\jp.co.bandainamcoent.BNEI0421\RAW")
    parser.add_argument("--thread", type=int, default=32)
    return parser.parse_args()

class Hash:
    @staticmethod
    def md5(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif hasattr(data, 'read'):
            data = data.read()
        return hashlib.md5(data).hexdigest()
    
class AESCipher:
    def __init__(self):
        self.key = hashlib.sha256("x5HFaJCJywDyuButLM0f".encode('utf-8')).digest()

    def decrypt(self, raw: bytes) -> bytes:
        iv, enc = raw[:16], raw[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(enc), 16)
        return decrypted
    
class Game_API:
    def __init__(self):
        self.API_URL = "https://api.asset.game-gakuen-idolmaster.jp"
        self.ASSET_URL = "https://object.asset.game-gakuen-idolmaster.jp"
        self.UNITY_VER = "2022.3.57f1"
        self.OCTO_KEY = "0jv0wsohnnsigttbfigushbtl3a8m7l5"

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"UnityPlayer/{self.UNITY_VER} (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
            "Accept-Encoding": "deflate, gzip",
            "Accept": "application/x-protobuf,x-octo-app/400",
            "X-OCTO-KEY": self.OCTO_KEY,
            "X-Unity-Version": self.UNITY_VER,
        })

        self.cipher = AESCipher()

    def _get(self, url, extra_headers=None, **kw):
        hdr = self.session.headers.copy()
        if extra_headers:
            hdr.update(extra_headers)
        return self.session.get(url, headers=hdr, **kw)
    
    def call_game(self, endpoint):
        url = self.API_URL + endpoint
        resp = self.session.get(url)
        resp.raise_for_status()

        raw = resp.content
        decrypted = self.cipher.decrypt(raw)

        db = octo_pb2.Database()
        db.ParseFromString(decrypted)
        return MessageToDict(db, preserving_proto_field_name=True)

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

def filter_existing(root, assets):
    to_dl_a = []
    to_dl_m = []
    skipped = 0
    total_bytes = 0

    print("Scanning existing files (MD5)…")
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Scanning", total=len(assets['assetBundleList']) + len(assets['resourceList']))
        for a in assets['assetBundleList']:
            dest = os.path.join(root, "a", a['name'] + '.unity3d')

            if os.path.exists(dest) and os.path.getsize(dest) == a['size']:
                with open(dest, "rb") as f:
                    if Hash.md5(f) == a['md5']:
                        skipped += 1
                        prog.update(task_id, advance=1)
                        continue

            to_dl_a.append(a)
            total_bytes += a['size']
            prog.update(task_id, advance=1)
        
        for a in assets['resourceList']:
            if a['name'].startswith('img_'):
                dest = os.path.join(root, 'm_image', a['name'])
            elif a['name'].startswith('sud_') and a['name'].endswith('.awb'):
                dest = os.path.join(root, 'm_audio', a['name'])
            elif a['name'].startswith('sud_') and a['name'].endswith('.acb'):
                dest = os.path.join(root, 'm_audio', a['name'])
            elif a['name'].startswith('mov_'):
                dest = os.path.join(root, 'm_video', a['name'])
            elif a['name'].startswith('adv_'):
                dest = os.path.join(root, 'm_adventure', a['name'])

            if os.path.exists(dest) and os.path.getsize(dest) == a['size']:
                with open(dest, "rb") as f:
                    if Hash.md5(f) == a['md5']:
                        skipped += 1
                        prog.update(task_id, advance=1)
                        continue
            
            to_dl_m.append(a)
            total_bytes += a['size']
            prog.update(task_id, advance=1)

    total_gib = total_bytes / (1024 ** 3)
    return to_dl_a, to_dl_m, skipped, total_gib

def download_many(root, assets_a, assets_m, workers):
    asset_api = Game_API()
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Downloading", total=len(assets_a) + len(assets_m))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_dest = {}
            for a in assets_a:
                url = f'/{a['objectName']}'
                dest = os.path.join(root, "a", a['name'] + '.unity3d')

                future = pool.submit(asset_api.call_asset, url)
                future_to_dest[future] = dest

            for a in assets_m:
                if a['name'].startswith('img_'):
                    dest = os.path.join(root, 'm_image', a['name'])
                elif a['name'].startswith('sud_') and a['name'].endswith('.awb'):
                    dest = os.path.join(root, 'm_audio', a['name'])
                elif a['name'].startswith('sud_') and a['name'].endswith('.acb'):
                    dest = os.path.join(root, 'm_audio', a['name'])
                elif a['name'].startswith('mov_'):
                    dest = os.path.join(root, 'm_video', a['name'])
                elif a['name'].startswith('adv_'):
                    dest = os.path.join(root, 'm_adventure', a['name'])

                url = f'/{a['objectName']}'
                future = pool.submit(asset_api.call_asset, url)
                future_to_dest[future] = dest

            for future in as_completed(future_to_dest):
                dest = future_to_dest[future]
                try:
                    content = future.result()
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(content)
                except Exception as e:
                    prog.console.log(f"[E]Error Saving {dest}: {e}")
                finally:
                    prog.update(task_id, advance=1)
                
if __name__ == "__main__":
    args = parse_args()
    print("Fetching Asset Manifest")
    asset_manifest = Game_API().call_game("/v2/pub/a/400/v/205000/list/0")
    
    to_dl_a, to_dl_m, skipped, total_gib = filter_existing(args.RAW, asset_manifest)
    print(f"Total: {len(to_dl_a) + len(to_dl_m)}, Skipped: {skipped}, Size: {total_gib:.2f} GiB")
    if not to_dl_a and not to_dl_m:
        print("Up to date")
        exit(0)
    
    download_many(args.RAW, to_dl_a, to_dl_m, args.thread)