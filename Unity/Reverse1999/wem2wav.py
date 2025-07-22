import os
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

def convert_one(src_path, dest_path, vgmstream_exe):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    cmd = [vgmstream_exe, '-o', dest_path, src_path]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"Converted: {src_path} -> {dest_path}")
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to convert {src_path}: {e.stderr.decode().strip()}")

def collect_tasks(input_root, output_root):
    tasks = []
    for dirpath, _, files in os.walk(input_root):
        for file in files:
            if file.lower().endswith('.wem'):
                rel_dir = os.path.relpath(dirpath, input_root)
                src_path = os.path.join(dirpath, file)
                wav_name = os.path.splitext(file)[0] + '.wav'
                dest_path = os.path.join(output_root, rel_dir, wav_name)
                tasks.append((src_path, dest_path))
    return tasks

def convert_wems(input_root, output_root, vgmstream_exe, workers):
    tasks = collect_tasks(input_root, output_root)
    total = len(tasks)
    print(f"Found {total} .wem files under {input_root}, converting with {workers} workers...")
    with ThreadPoolExecutor(max_workers=workers) as exec:
        futures = [exec.submit(convert_one, src, dst, vgmstream_exe) for src, dst in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Batch-convert .wem to .wav with multithreading")
    parser.add_argument('--input_root', default=r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\audios\Android",
                        help="Source directory of .wem files")
    parser.add_argument('--output_root', default=r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\audios\Android_WAV",
                        help="Destination directory for .wav files")
    parser.add_argument('--vgmstream_exe', default=r"D:\Tools\vgmstream-win64\vgmstream-cli.exe",
                        help="Path to vgmstream-cli executable")
    parser.add_argument('--workers', type=int, default=40,
                        help="Number of parallel threads (default: number of CPU cores)")
    args = parser.parse_args()

    convert_wems(
        input_root=args.input_root,
        output_root=args.output_root,
        vgmstream_exe=args.vgmstream_exe,
        workers=args.workers
    )