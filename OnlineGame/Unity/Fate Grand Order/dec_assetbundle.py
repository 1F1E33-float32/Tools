import os
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dec_common import decrypt_and_decompress, get_interleaved_split
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default=r"E:\Game_Dataset\com.aniplex.fategrandorder\RAW")
    parser.add_argument("--output", type=str, default=r"E:\Game_Dataset\com.aniplex.fategrandorder\DEC")
    return parser.parse_args()

base_data, base_top, stage_data, stage_top = get_interleaved_split()

columns = (SpinnerColumn(), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>6.2f}%", TimeElapsedColumn(), "•", TimeRemainingColumn(), TextColumn("[bold blue]{task.description}"))

def read_version_info(root):
    storage_path = os.path.join(root, "3_AssetStorage.txt")
    with open(storage_path, "r", encoding="utf-8") as fp:
        lines = [ln.strip() for ln in fp if ln.strip()]
    data = [[field.strip() for field in line.split(',')] for line in lines[2:]]
    return data

def other_home_building(data):
    bts = data.encode("utf‑8")
    home = bytearray(32)
    info = bytearray(32)

    for i, b in enumerate(bts[:32]):
        if i == 0:
            home[i] = b
        else:
            info[i] = b
    return bytes(home), bytes(info)

# 有额外key
def mouse_game4_with_key(data, key):
    home, info = other_home_building(key)
    array = decrypt_and_decompress(data, home, info, False)
    return array

# 无额外key
def mouse_game4(data):
    array = decrypt_and_decompress(data, base_data, base_top, False)
    buf = bytearray(array)
    for i in range(0, len(buf), 2):
        if i + 1 >= len(buf):
            break
        b, b2      = buf[i], buf[i + 1]
        buf[i]     = b2 ^ 0xD2
        buf[i + 1] = b  ^ 0xCE
    return bytes(buf)
    
def process_ab(ab, root, output, prog, task_id):
    file_name = ab["FileName"]
    prog.update(task_id, description=f"{file_name}")
    ab_path = os.path.join(root, file_name + ".unity3d")
    with open(ab_path, "rb") as f:
        data = f.read()

    if ab["EXKey"]:
        array = mouse_game4_with_key(data, ab["EXKey"])
    else:
        array = mouse_game4(data)

    output_path = os.path.join(output, file_name + ".unity3d")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(array)

    prog.update(task_id, advance=1)

def main():
    args = args_parser()

    with open(os.path.join(args.root, "2_assetbundleKey.json"), "r", encoding="utf-8") as f:
        key_list = json.load(f)
    key_index = { key["id"]: key["decryptKey"] for key in key_list }

    txt_lines = read_version_info(args.root)
    result = []
    for lines in txt_lines:
        if lines[4].endswith(".usm") or lines[4].endswith(".cpk.bytes"):
            continue
        elif len(lines) == 6:
            decryptkey = key_index.get(lines[5])
            result.append({"FileName": lines[4], "EXKey": decryptkey})
        else:
            result.append({"FileName": lines[4], "EXKey": None})

    with Progress(*columns) as prog:
        task_id = prog.add_task("解密中...", total=len(result))
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_ab, ab, args.root, args.output, prog, task_id) for ab in result]
            for future in as_completed(futures):
                future.result()

if __name__ == "__main__":
    main()