import os
import json
import argparse
from tqdm import tqdm
from glob import glob


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    p.add_argument("-VO", type=str, default=r"D:\Fuck_galgame\voice")
    p.add_argument("-op", type=str, default=r"D:\Fuck_galgame\index.json")
    return p.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = (
        text.replace('『', '')
        .replace('』', '')
        .replace('「', '')
        .replace('」', '')
        .replace('（', '')
        .replace('）', '')
        .replace('\n', '')
        .replace('　', '')
    )
    return text


def load_lines(path):
    with open(path, 'r', encoding='cp932') as f:
        lines = f.readlines()
    return [ln.lstrip() for ln in lines if not ln.startswith('//')]


def process_char(lines, results):
    idx = 1
    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split()

        name = "".join(parts[:-1])
        flag = parts[-1]

        if flag != "0":
            index = f"{idx:02d}"
            results[index] = name
            idx += 1


def process_vo(base_dir, results):
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        for filename in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, filename)
            if not os.path.isfile(file_path):
                continue

            name, _ = os.path.splitext(filename)
            if folder not in results:
                results[folder] = []
            results[folder].append(name)


def _voice_exists(folder: str, voice: str, vo_index: dict) -> bool:
    names = vo_index.get(folder)
    if not names:
        return False

    v = voice or ""
    v_strip = v.lstrip('0')
    v_z4 = v.zfill(4) if v else v

    candidates = {v, v_strip, v_z4}

    for c in candidates:
        if c in names:
            return True

    # fallback suffix match (covers prefixes)
    for n in names:
        for c in candidates:
            if c and n.endswith(c):
                return True
    return False


def process_script(lines, results, results_char):
    fw_digits = '０１２３４５６７８９'
    ascii_digits = '0123456789'
    tran = str.maketrans({f: a for f, a in zip(fw_digits, ascii_digits)})

    char_to_index = {name: idx for idx, name in results_char.items()}

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        parts = line.split('　')  # 全角空格切分
        speaker = None
        voice = None

        if len(parts) == 3:
            raw_voice = parts[1].strip('（）')
            voice = raw_voice.translate(tran)
            speaker = parts[2]

        # 普通行：名字 + 语音编号
        elif len(parts) == 2:
            raw_voice = parts[1].strip('（）')
            voice = raw_voice.translate(tran)

            # 语音编号全零，跳过整个段落
            if voice == '0000':
                i += 1
                continue

            speaker = parts[0]

        else:
            # 既不是 2 段也不是 3 段，则跳过
            i += 1
            continue

        folder = char_to_index.get(speaker)
        if folder is None:
            # 如果这个 speaker 没在 results_char 里，也跳过
            i += 1
            continue

        # 收集从下一行开始到空行之间的台词
        tmp = []
        j = i + 1
        while j < n and lines[j].strip():
            tmp.append(lines[j])
            j += 1

        text = text_cleaning(''.join(tmp))

        results.append({
            "Speaker": speaker,
            "Folder": folder,
            "Voice": voice,
            "Text": text
        })
        i = j + 1


def main(JA_dir, VO_dir, op_json):
    file_script = glob(f"{JA_dir}/**/ACT_*.txt", recursive=True)
    file_char = f"{JA_dir}/charaid.tbl"

    results_char = {}
    lines_char = load_lines(file_char)
    process_char(lines_char, results_char)

    result_vo = {}
    process_vo(VO_dir, result_vo)
    voice_index = {k: set(v) for k, v in result_vo.items()}

    results = []
    for fn in tqdm(file_script):
        lines = load_lines(fn)
        process_script(lines, results, results_char)
        if not results:
            continue

    # --- Filter out nonexistent voices ---
    filtered_results = []
    missing = 0
    for entry in results:
        folder = entry["Folder"]
        voice = entry["Voice"]
        if not voice or voice == '0000':
            missing += 1
            continue
        if not _voice_exists(folder, voice, voice_index):
            missing += 1
            continue
        filtered_results.append(entry)

    # Deduplicate by (Folder, Voice)
    seen = set()
    unique_results = []
    for entry in filtered_results:
        key = (entry["Folder"], entry["Voice"])
        if key in seen:
            continue
        seen.add(key)
        unique_results.append(entry)

    print(f"Filtered out {missing} entries with missing voice files; kept {len(unique_results)}.")

    with open(op_json, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.VO, args.op)