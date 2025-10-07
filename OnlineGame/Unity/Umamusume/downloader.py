from time import time

import requests
from requests.adapters import HTTPAdapter
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from urllib3.util.retry import Retry

columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"E:\Game_Dataset\jp.co.bandainamcoent.BNEI0242\RAW")
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


if __name__ == "__main__":
    args = parse_args()
