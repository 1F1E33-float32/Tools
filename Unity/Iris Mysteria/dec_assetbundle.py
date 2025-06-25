import os
import argparse
from Crypto.Cipher import AES
from concurrent.futures import ThreadPoolExecutor

from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)

ApiKey = bytes([239,192,238,121,215,59,66,42,12,127,225,203,42,14,178,182,16,8,28,34,176,50,8,0,11,191,164,76,12,174,147,41])

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", default=r"D:\Dataset_Game\あいりすミスティリア！ 〜少女のつむぐ夢の秘跡〜\RAW")
    parser.add_argument("--EXP", default=r"D:\Dataset_Game\あいりすミスティリア！ 〜少女のつむぐ夢の秘跡〜\DEC")
    return parser.parse_args()

def decryptdata(key: bytes, data: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC)
    plaintext = cipher.decrypt(data)
    return plaintext[16:]

def decrypt_and_write(in_path: str, out_path: str):
    try:
        with open(in_path, "rb") as inf:
            encrypted = inf.read()
        decrypted = decryptdata(ApiKey, encrypted)
        with open(out_path, "wb") as outf:
            outf.write(decrypted)
    except Exception as e:
        # Log the error and continue
        print(f"Failed to decrypt {in_path}: {e}")

def main():
    args = parse_args()
    input_root = os.path.abspath(args.RAW)
    output_root = os.path.abspath(args.EXP)

    os.makedirs(output_root, exist_ok=True)

    # Gather all file paths
    file_pairs = []
    for dirpath, _, filenames in os.walk(input_root):
        rel_dir = os.path.relpath(dirpath, input_root)
        for fname in filenames:
            in_path = os.path.join(dirpath, fname)
            out_dir = os.path.join(output_root, rel_dir)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, fname)
            file_pairs.append((in_path, out_path))

    total_files = len(file_pairs)
    if total_files == 0:
        print("No files found to decrypt.")
        return

    columns = (SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), "•", TimeRemainingColumn())

    # Run decryption with multithreading and shared progress bar
    with Progress(*columns) as progress:
        task_id = progress.add_task("Decrypting files", total=total_files)
        with ThreadPoolExecutor() as executor:
            futures = []
            for in_path, out_path in file_pairs:
                future = executor.submit(decrypt_and_write, in_path, out_path)
                future.add_done_callback(lambda _f: progress.advance(task_id))
                futures.append(future)

            for f in futures:
                f.result()

    print(f"Finished decrypting {total_files} files to {output_root}")

if __name__ == "__main__":
    main()
