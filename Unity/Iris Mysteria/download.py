import os
import hmac
import json
import random
import urllib
import zlib
import requests
import UnityPy
import argparse
from base64 import b64decode
from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from phpserialize3 import loads as phpload

from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)
columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"D:\Dataset_Game\あいりすミスティリア！ 〜少女のつむぐ夢の秘跡〜\RAW")
    parser.add_argument("--thread", type=int, default=16)
    return parser.parse_args()

class IrisDecryptor:
    def __init__(self, api_key: bytes):
        self.api_key = api_key

    def decrypt_data(self, key: bytes, data: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_CBC)
        return cipher.decrypt(data)[16:]

    def decrypt_olg_session(self, cookie_value: str) -> str:
        blob = urllib.parse.unquote(cookie_value)
        payload = json.loads(b64decode(blob))
        iv = b64decode(payload['iv'])
        encrypted = b64decode(payload['value'])
        plain = self.decrypt_data(self.api_key, iv + encrypted)
        plain = unpad(plain, AES.block_size)
        return phpload(plain.decode())

    def decrypt_response_data(self, session_id: str, cipher_data: bytes) -> bytes:
        aes_key = hmac.new(self.api_key, session_id.encode(), sha256).digest()
        decrypted = self.decrypt_data(aes_key, cipher_data)
        return zlib.decompress(decrypted, 15 + 32)

class Game_API:
    def __init__(self):
        self.api_key = bytes([54,88,54,50,52,85,89,111,79,122,84,112,74,79,68,108,119,106,49,116,55,111,70,103,83,76,79,87,122,78,98,122])
        self.pf_type = '5'
        self.user_agent = 'UnityPlayer/2021.3.36f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)'
        self.app_version = '3.4.50'
        self.base_url = 'https://rkyfxfex.aimia.dmmgames.com/'
        self.asset_url = 'https://rkyfxfex.cdn.aimia.dmmgames.com/'

        self.decryptor = IrisDecryptor(self.api_key)
        self.session_id = ''
        self.headers = {
            'app-version': self.app_version,
            'pf-type': self.pf_type,
            'User-Agent': self.user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'X-Unity-Version': '2021.3.36f1',
        }

        # Initialize HTTP session
        self.session = self._init_session()

    def _init_session(self):
        sess = requests.Session()
        sess.mount('http://', HTTPAdapter(max_retries=10))
        sess.mount('https://', HTTPAdapter(max_retries=10))
        sess.headers.update(self.headers)
        return sess

    def _get(self, url: str, extra_headers: dict = None, **kwargs) -> requests.Response:
        headers = self.headers.copy()
        if extra_headers:
            headers.update(extra_headers)
        return self.session.get(url, headers=headers, **kwargs)

    def call_game(self, endpoint: str) -> dict:
        base = urllib.parse.urljoin(self.base_url, endpoint)
        sep = '&' if '?' in base else '?'
        url = f"{base}{sep}v={''.join(random.choices('0123456789', k=8))}"
        resp = self._get(url)

        # Decrypt and update session_id
        raw_cookie = resp.cookies.get('olg_session')
        self.session_id = self.decryptor.decrypt_olg_session(raw_cookie)

        # Decrypt response content
        decrypted = self.decryptor.decrypt_response_data(self.session_id, resp.content)
        return json.loads(decrypted)
    
    def call_index_assetbundle(self, endpoint: str) -> dict:
        base = urllib.parse.urljoin(self.asset_url, endpoint)
        sep = '&' if '?' in base else '?'   
        url = f"{base}{sep}x={''.join(random.choices('0123456789', k=18))}"
        resp = self._get(url).content

        env = UnityPy.load(resp).objects
        for obj in env:
            if obj.type.name == "AssetBundleManifest":
                mani = obj.read()
                break
        names = [name[1] for name in mani.AssetBundleNames]
        infos = [info[1] for info in mani.AssetBundleInfos]
        result = []
        for name, info in zip(names, infos):
            hex = info.AssetBundleHash
            hex = bytes(getattr(hex, f"bytes_{i}_") for i in range(16)).hex()
            result.append({'name': name, 'hash': hex})
        return result
    
    def call_index_sound(self, endpoint: str) -> dict:
        base = urllib.parse.urljoin(self.asset_url, endpoint)
        sep = '&' if '?' in base else '?'
        url = f"{base}{sep}v={''.join(random.choices('0123456789', k=8))}"

        resp = self._get(url)
        data = resp.json()

        result = []
        for entry in data['entries']:
            result.append({
                'path': entry['path'],
                'hash': entry['hash'],
                'size': entry['size']
            })

        return result
    
    def call_asset(self, endpoint: str) -> bytes:
        base = urllib.parse.urljoin(self.asset_url, endpoint)
        resp = self._get(base, allow_redirects=True)
        return resp.content

def download_many_assetbundle(root, assets, version, workers):
    asset_api = Game_API()
    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Downloading", total=len(assets))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_dest = {}
            for a in assets:
                url = f"{version}/assetbundle/Windows/{a['name']}.encrypted"
                dest = os.path.join(root, 'assetbundle', a["name"])

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

def download_many_sound(root, assets, version, endpoint, workers):
    asset_api = Game_API()

    # e.g. endpoint = "12345/assetbundle/sound/PC/SCENARIO/manifest.json"
    asset_type = endpoint.strip("/").split("/")[-2]

    with Progress(*columns, transient=True) as prog:
        task_id = prog.add_task("Downloading", total=len(assets))

        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_dest = {}
            for entry in assets:
                # entry['path'] (or entry['Path'] if you used the other naming)
                path = entry.get("path", entry.get("Path"))

                # construct URL & local directory dynamically
                url  = f"{version}/assetbundle/sound/PC/{asset_type}/{path}"
                dest = os.path.join(root, asset_type, path)

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
                    prog.console.log(f"[E] Error saving {dest}: {e}")
                finally:
                    prog.update(task_id, advance=1)

if __name__ == "__main__":
    args = parse_args()
    client = Game_API()

    data = client.call_game('game_type')
    version = data['versions']['assetversion']
    Game_API.app_version = data['versions']['appversion']
    
    mai = client.call_index_assetbundle(f'{version}/assetbundle/Windows/Windows')

    download_many_assetbundle(args.RAW, mai, version,  args.thread)

    #voice_mai = client.call_index_voice(f'{version}/assetbundle/sound/PC/VOICE/manifest.json')
    #download_many_voice(args.RAW, voice_mai, version, args.thread)

    endpoint = f"{version}/assetbundle/sound/PC/SCENARIO/manifest.json"
    scenario_assets = client.call_index_sound(endpoint)
    download_many_sound(args.RAW, scenario_assets, version, endpoint, args.thread)