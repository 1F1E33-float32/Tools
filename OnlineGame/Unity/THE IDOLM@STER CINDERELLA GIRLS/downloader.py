import io
import os
import uuid
import time
import struct
import base64
import random
import sqlite3
import msgpack
import hashlib
import requests
import argparse
import lz4.block
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)
columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"E:\Game_Dataset\jp.co.bandainamcoent.BNEI0242\RAW")
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

    @staticmethod
    def sha1(data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif hasattr(data, 'read'):
            data = data.read()
        return hashlib.sha1(data).hexdigest()
    
class Rijndael:
    @staticmethod
    def encrypt(data, key, iv, key_size=128):
        if key_size not in (128, 256):
            raise ValueError("key_size must be 128 or 256")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        text = pad(data, AES.block_size)
        text = cipher.encrypt(text)
        return text

    @staticmethod
    def decrypt(data, key, iv, key_size=128):
        if key_size not in (128, 256):
            raise ValueError("key_size must be 128 or 256")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        text = cipher.decrypt(data)
        text = unpad(text, AES.block_size)
        return text

class Cryptographer:
    def encode(s):
        length_hex = format(len(s), 'x').zfill(4)
        body = []
        for ch in s:
            body.append(str(random.randint(0,9)))
            body.append(str(random.randint(0,9)))
            body.append(chr(ord(ch) + 10))
            body.append(str(random.randint(0,9)))
        suffix = str(random.randint(10_000_000, 99_999_999)) + str(random.randint(10_000_000, 99_999_999))
        return length_hex + ''.join(body) + suffix
    
class Game_API:
    def __init__(self):
        self.API_URL   = "https://apis.game.starlight-stage.jp"
        self.ASSET_URL = "https://asset-starlight-stage.akamaized.net"

        self.UNITY_VER = "2022.3.40f1"
        self.APP_VER   = "11.2.5"
        self.RES_VER   = "10127900"

        self.GUID      = uuid.uuid4().hex
        self.VIEWER_ID     = "0"
        self.VIEWER_ID_KEY = "s%5VNQ(H$&Bqb6#3+78h29!Ft4wSg)ex"
        self.VIEWER_ID_IV  = "".join(str(random.randint(1, 9)) for _ in range(16))

        self.USER_ID  = "0"
        self.SID      = "0"
        self.SID_SALT = "r!I@nt8e5i="

        self.session = requests.Session()
        retries = Retry(total=100, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": f"UnityPlayer/{self.UNITY_VER} (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "X-Unity-Version": self.UNITY_VER,
        })

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

    def call_game(self, endpoint):
        args = {"timezone": "09:00:00"}

        vid_enc = Rijndael.encrypt(self.VIEWER_ID.encode(), self.VIEWER_ID_KEY.encode(), self.VIEWER_ID_IV.encode(), key_size=128)
        args["viewer_id"] = self.VIEWER_ID_IV + base64.b64encode(vid_enc).decode()

        packed = base64.b64encode(msgpack.packb(args, use_bin_type=True)).decode()
        key32  = "".join(str(random.randint(0, 9)) for _ in range(32)).encode()
        iv16   = bytes(int(self.GUID[i:i+2], 16) for i in range(0, 32, 2))

        cipher = Rijndael.encrypt(packed.encode(), key32, iv16, key_size=128)
        body_b64 = base64.b64encode(cipher + key32).decode()

        api_headers = {
            "Processor-Type": "arm64e",
            "User-Agent": "BNEI0242/425 CFNetwork/3826.500.111.2.2 Darwin/24.4.0",
            "Param": Hash.sha1(self.GUID + self.VIEWER_ID + endpoint + packed),
            "Device-Name": "iPhone15,2",
            "Graphics-Device-Name": "Apple A16 GPU",
            "Platform-Os-Version": "iOS 18.4.1",
            "Keychain": "",
            "Udid": Cryptographer.encode(self.GUID),
            "Device-Id": "11111111-1111-1111-1111-111111111111",
            "Sid": Hash.md5(self.SID + self.SID_SALT),
            "Carrier": "--",
            "Ip-Address": "127.0.0.1",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "App-Ver": self.APP_VER,
            "Res-Ver": self.RES_VER,
            "User-Id": Cryptographer.encode(self.USER_ID),
            "Content-Type": "application/octet-stream",
            "Device": "1",
            "Idfa": "00000000-0000-0000-0000-000000000000",
            "Connection": "keep-alive",
        }

        resp_b64 = self._post(self.API_URL + endpoint, data=body_b64, extra_headers=api_headers).text

        src      = base64.b64decode(resp_b64)
        key_resp = src[-32:]
        cipher   = src[:-32]
        plain    = Rijndael.decrypt(cipher, key_resp, iv16)
        result   = msgpack.unpackb(base64.b64decode(plain), raw=False)
        return result

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

def table_to_dict(data, table_name):
    data = io.BytesIO(data)
    num1, uncompressed_size, _, num2 = struct.unpack('<IIII', data.read(16))
    if num1 != 100 or num2 != 1:
        raise ValueError('invalid data')
    compressed = data.read()
    db_bytes = lz4.block.decompress(compressed, uncompressed_size=uncompressed_size)

    conn = sqlite3.connect(':memory:')
    try:
        conn.deserialize(db_bytes)
    except AttributeError:
        raise RuntimeError('SQLite 序列化 API 不可用：需 Python 3.11+ 且底层 SQLite ≥3.36.0')
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    result = [dict(row) for row in cur.fetchall()]
    return result

def parse_manifest(data):
    data = data.decode('utf-8')
    lines = data.strip().split('\n')
    parsed = []

    for line in lines:
        parts = line.split(',')
        item = {
            "name": parts[0],
            "hash": parts[1],
        }
        parsed.append(item)
    return parsed

def filter_existing(root, assets):
    to_dl = []
    skipped = 0
    total_bytes = 0

    print("Scanning existing files (MD5)…")
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Scanning", total=len(assets))
        for a in assets:
            if a['name'].endswith(".unity3d"):
                dest = os.path.join(root, "a", a['name'])

            elif a['name'].endswith(".acb") or a['name'].endswith(".awb") or a['name'].endswith(".bytes"):
                dest = os.path.join(root, a['name'])

            elif a['name'].endswith(".usm"):
                dest = os.path.join(root, a['name'])
                
            elif a['name'].endswith(".mdb"):
                dest = os.path.join(root, "master", a["name"])
                
            else:
                print(f"[E] Unknown file type: {a['name']}")
                continue

            if os.path.exists(dest) and os.path.getsize(dest) == a['size']:
                with open(dest, "rb") as f:
                    if Hash.md5(f) == a['hash']:
                        skipped += 1
                        prog.update(task_id, advance=1)
                        continue

            to_dl.append(a)
            total_bytes += a['size']
            prog.update(task_id, advance=1)

    total_gib = total_bytes / (1024 ** 3)
    return to_dl, skipped, total_gib

def download_many(root, assets, workers):
    asset_api = Game_API()
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Downloading", total=len(assets))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_dest = {}
            for a in assets:
                if a['name'].endswith(".unity3d"):
                    url = f"/dl/resources/AssetBundles/{a['hash'][:2]}/{a['hash']}"
                    dest = os.path.join(root, "a", a['name'])

                elif a['name'].endswith(".acb") or a['name'].endswith(".awb") or a['name'].endswith(".bytes"):
                    url = f"/dl/resources/Sound/{a['hash'][:2]}/{a['hash']}"
                    dest = os.path.join(root, a['name'])

                elif a['name'].endswith(".usm"):
                    url = f"/dl/resources/Movie/{a['hash'][:2]}/{a['hash']}"
                    dest = os.path.join(root, a['name'])
                    
                elif a['name'].endswith(".mdb"):
                    url = f"/dl/resources/Generic/{a['hash'][:2]}/{a['hash']}"
                    dest = os.path.join(root, "master", a["name"])

                else:
                    print(f"[E] Unknown file type: {a['name']}")
                    continue

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
    print("Fetching Asset Version")
    asset_version = Game_API().call_game("/load/title")['data_headers']['RES_VER']
    print("Fetching Asset Manifest")
    asset_manifest = Game_API().call_asset(f"/dl/{asset_version}/manifests/all_dbmanifest")
    print("Fetching Asset Database")
    asset_db = Game_API().call_asset(f"/dl/{asset_version}/manifests/{parse_manifest(asset_manifest)[2]['name']}")
    asset_db = table_to_dict(asset_db, "manifests")
    
    to_dl, skipped, total_gib = filter_existing(args.RAW, asset_db)
    print(f"Total: {len(to_dl)}, Skipped: {skipped}, Size: {total_gib:.2f} GiB")
    if not to_dl:
        print("Up to date")
        exit(0)
    
    download_many(args.RAW, to_dl, args.thread)