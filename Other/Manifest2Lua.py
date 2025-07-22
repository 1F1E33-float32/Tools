import sys
import vdf
import requests
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config"
if not CONFIG_PATH.is_file():
    print(f"❌ 找不到配置文件：{CONFIG_PATH}")
    sys.exit(1)
GITHUB_TOKEN = CONFIG_PATH.read_text(encoding="utf-8").strip()
if not GITHUB_TOKEN:
    print("❌ 配置文件中未找到有效的 GitHub Token")
    sys.exit(1)

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
})
# ——————————————————————————————— #

REPOS = [
    "SteamAutoCracks/ManifestHub",
    "ikun0014/ManifestHub",
    "Auiowu/ManifestAutoUpdate",
    "tymolu233/ManifestAutoUpdate-fix",
]

def github_json(url, timeout=10):
    resp = SESSION.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def download_file(repo, sha, path, *, save_dir=None, save=False, timeout=20):
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
    try:
        resp = SESSION.get(url, timeout=timeout)
        resp.raise_for_status()
        if save and save_dir:
            out_path = save_dir / path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(resp.content)
        return resp.content
    except requests.RequestException as e:
        print(f"❌ {path} – {e}")
        return None

def parse_vdf_keys(raw):
    data = vdf.loads(raw.decode("utf-8", errors="ignore"))
    depots = data.get("depots", {})
    return [
        (depot_id, info["DecryptionKey"])
        for depot_id, info in depots.items()
        if info.get("DecryptionKey")
    ]

def collect_repo_data(appid, repo, save_dir):
    print(f"\nℹ️  Checking {repo} …")
    branch_url = f"https://api.github.com/repos/{repo}/branches/{appid}"
    try:
        branch = github_json(branch_url)
    except requests.RequestException as e:
        print(f"⚠️  Branch not found or network error: {e}")
        return [], False

    sha = branch["commit"]["sha"]
    tree_url = f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"
    try:
        items = github_json(tree_url).get("tree", [])
    except requests.RequestException as e:
        print(f"⚠️  Tree fetch failed: {e}")
        return [], False

    depot_keys = []
    manifest_found = False

    for item in items:
        if item.get("type") != "blob":
            continue

        pth: str = item["path"]
        base = Path(pth).name.lower()

        if pth.endswith(".manifest"):
            download_file(repo, sha, pth, save_dir=save_dir, save=True)
            manifest_found = True

        elif base in {"key.vdf", "config.vdf"}:
            raw = download_file(repo, sha, pth)  # no save
            if raw:
                depot_keys.extend(parse_vdf_keys(raw))

    return depot_keys, manifest_found

def fetch_all(appid):
    save_dir = Path.cwd() / appid
    all_depot_keys = []

    for repo in REPOS:
        keys, has_manifest = collect_repo_data(appid, repo, save_dir)
        if keys:
            print(f"✅ {len(keys)} depot key(s) in {repo}")
            all_depot_keys = keys
        if keys or has_manifest:
            break
    else:
        print("❌  Nothing found in any repository.")

    return all_depot_keys, save_dir

def build_lua(appid, keys, save_dir):
    lines = [f"addappid({appid})"]

    manifest_map = {}
    for mfile in save_dir.rglob("*.manifest"):
        try:
            depot, manifestid = mfile.stem.split("_", 1)
            manifest_map.setdefault(depot, manifestid)
        except ValueError:
            continue

    for depot_id, key in keys:
        lines.append(f"addappid({depot_id},1,\"{key}\")")
        manifest_id = manifest_map.get(depot_id)
        if manifest_id:
            lines.append(f"setManifestid({depot_id},\"{manifest_id}\",0)")

    lua_path = save_dir / f"{appid}.lua"
    lua_path.write_text("\n".join(lines), encoding="utf-8")
    return lua_path

if __name__ == "__main__":
    appid = input("Enter AppID: ").strip()
    if not appid.isdigit():
        print("❌  Invalid AppID – numbers only.")
        sys.exit(1)

    depot_keys, save_dir = fetch_all(appid)
    if not depot_keys:
        print("❌  No depot keys found.")
        sys.exit(1)

    lua_path = build_lua(appid, depot_keys, save_dir)
    print(f"\n🎉 Lua unlock file written to: {lua_path}")