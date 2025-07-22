import os
import json
import urllib
import requests
import argparse
import base64
import blackboxprotobuf as bbpb

from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)
columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"D:\Dataset_Game\BrownDust2\RAW")
    parser.add_argument("--thread", type=int, default=32)
    return parser.parse_args()

class Game_API:
    def __init__(self):
        self.user_agent = 'UnityPlayer/2022.3.22f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)'
        self.app_version = '3.4.50'
        self.base_url = 'https://mt.bd2.pmang.cloud/'
        self.asset_url = 'https://bd2-cdn.akamaized.net/ServerData/StandaloneWindows64/HD/'

        self.session_id = ''
        self.headers = {
            'app-version': self.app_version,
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
    
    def _put(self, url: str, data, extra_headers: dict = None, **kwargs) -> requests.Response:
        headers = self.headers.copy()
        if extra_headers:
            headers.update(extra_headers)
        return self.session.put(url, headers=headers, data=data, **kwargs)

    def call_game(self, endpoint: str) -> dict:
        base = urllib.parse.urljoin(self.base_url, endpoint)

        body = {
            "1": 2,
            "2": 8,
            "3": "2.0.28",
            "5": "419423330|5063|WEB|KR|d8dbd6d779a1e794cdb3f16b0b545cc13ab14f33|1750835579883",
            "6": 5
            }

        body_def = {
            "1": {"type": "int",    "name": ""},
            "2": {"type": "int",    "name": ""},
            "3": {"type": "string", "name": ""},
            "5": {"type": "string", "name": ""},
            "6": {"type": "int",    "name": ""}
            }
        unk_protobuf = bbpb.encode_message(body, body_def)
        unk_protobuf_b64 = base64.b64encode(unk_protobuf)

        resp = self._put(base, unk_protobuf_b64).content
        resp_b64= json.loads(resp.decode('utf-8'))['data']
        resp_bytes = base64.b64decode(resp_b64)

        version = bbpb.decode_message(resp_bytes)[0]['1']['3']
        return version
    
    def call_index_assetbundle(self, endpoint: str) -> dict:
        #base = urllib.parse.urljoin(self.asset_url, endpoint)
        #resp = self._get(base).content
        #index_json = json.loads(resp.decode('utf-8'))['m_InternalIds']
        with open(r"Unity\Brown Dust 2\catalog_alpha.json", "r", encoding="utf-8") as f:
            index_json = json.load(f)['m_InternalIds']

        result = []
        for item in index_json:
            if item.endswith('.bundle') and r"{BDNetwork.CdnInfo.Info}" in item:
                item = item.split("\\")[-1]
                result.append(item)
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
                url = f"{version}/{a}"
                dest = os.path.join(root, a)

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
    client = Game_API()

    version = client.call_game('MaintenanceInfo')
    
    mai = client.call_index_assetbundle(f'{version}/catalog_alpha.json')

    download_many_assetbundle(args.RAW, mai, version, args.thread)