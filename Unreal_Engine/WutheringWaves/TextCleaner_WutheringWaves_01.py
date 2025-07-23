import argparse
import subprocess
from pathlib import Path
from multiprocessing import Process

SUBPATHS = [
    Path("Client/Content/Aki/WwiseAudio_Generated/WwiseExternalSource"),
    Path("Client/Content/Aki/WwiseAudio_Generated/Media"),
]

def convert_wem_to_wav(src_wem, vgmstream_cli):
    dst_wav = src_wem.with_suffix(".wav")
    subprocess.run([str(vgmstream_cli), str(src_wem), "-o", str(dst_wav)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"完成：{dst_wav}"

def collect_wem_files(root: Path):
    files = []
    for sp in SUBPATHS:
        full = root / sp
        if full.exists():
            files.extend(full.rglob("*.wem"))
    return files

def worker(file_list, vgm_cli):
    for f in file_list:
        try:
            msg = convert_wem_to_wav(f, vgm_cli)
            if msg:
                print(msg)
        except Exception as e:
            print(f"[失败] {f} -> {e}")

def chunk_list(lst, n):
    if n <= 0:
        n = 1
    size = (len(lst) + n - 1) // n  # ceil
    return [lst[i:i + size] for i in range(0, len(lst), size)]

def main(root_dir, vgm_cli, workers):
    root_dir = Path(root_dir).resolve()
    vgm_cli = Path(vgm_cli).resolve()

    wem_files = collect_wem_files(root_dir)
    chunks = chunk_list(wem_files, workers)

    procs = []
    for chunk in chunks:
        p = Process(target=worker, args=(chunk, vgm_cli))
        procs.append(p)
        p.start()

    for p in procs:
        p.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir",      default=r"D:/Dataset_Game/WutheringWaves")
    parser.add_argument("--vgmstream_cli", default=r"D:\Tools\vgmstream-win64\vgmstream-cli.exe")
    parser.add_argument("--workers",       default=20)
    args = parser.parse_args()

    main(args.root_dir, args.vgmstream_cli, args.workers)