import re
import json
import chardet
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    p.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    p.add_argument("-ft", type=float, default=0)
    return p.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '').replace('\n', '')
    text = text.replace('　', '')
    return text

def guess_encoding(path):
    with open(path, 'rb') as f:
        raw = f.read()
    enc = chardet.detect(raw)['encoding']
    return enc

def load_lines(path):
    try:
        with open(path, 'r', encoding=guess_encoding(path)) as f:
            lines = f.readlines()
    except (UnicodeDecodeError, TypeError):
        with open(path, 'r', encoding='cp932') as f:
            lines = f.readlines()
    return [ln.lstrip() for ln in lines]


def process_type0(lines, results):
    current_voice = None

    for line in lines:
        voice_m = re.search(r'cvon\s*\(\s*"([^"]+)"\s*\)', line)
        if voice_m:
            current_voice = voice_m.group(1)
            continue

        dlg_m = re.search(r'\[([^]]+)\]「([^」]*)」', line)
        if dlg_m and current_voice:
            speaker = dlg_m.group(1)
            raw_text = dlg_m.group(2)

            text = text_cleaning(raw_text)

            if text:
                results.append({
                    "Speaker": speaker,
                    "Voice":   current_voice,
                    "Text":    text
                })

PROCESSORS = {
    0:   process_type0,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.scr", recursive=True)

    results = []
    for fn in tqdm(filelist):
        lines = load_lines(fn)

        processor(lines, results)

        if not results:
            continue

    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(op_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op, args.ft)