import re
import os
import json
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-ft", type=int, default=0)
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\{([^:]*):[^}]*\}|\{(.*?);.*?\}', r'\1', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace('\\n', '')
    return text

def symbol_cleaning(text):
    text = text.replace("%K", "").replace("%P", "").replace("%LR", "").replace(r"%LF", "")
    return text

def load_lines(path):
    with open(path, 'r', encoding='cp932') as f:
        lines = f.readlines()
    return lines

def process_type0(lines, results):
    for i, line in enumerate(lines):
        if line.strip().startswith("CharMessageStart"):
            Speaker = None
            Voice   = None
            Text    = None

            # scan until next CharMessageStart or end‐of‐file
            for j in range(i+1, len(lines)):
                l = lines[j].strip()

                # if we hit another block start, bail out
                if l.startswith("CharMessageStart"):
                    break

                # SoundEffect: second arg is filename, drop the extension
                if l.startswith("SoundEffect"):
                    m = re.search(r"SoundEffect\s*\([^,]+,\s*([^,]+)\s*,", l)
                    if m:
                        Voice = os.path.splitext(m.group(1))[0]

                # SetDisplayName: second arg is the speaker name
                elif l.startswith("SetDisplayName"):
                    m = re.search(r"SetDisplayName\s*\([^,]+,\s*['\"]([^'\"]+)['\"]\)", l)
                    if m:
                        Speaker = symbol_cleaning(m.group(1))

                # DisplayMessage: the very next line is the text
                elif l.startswith("DisplayMessage"):
                    if j+1 < len(lines):
                        raw = lines[j+1].strip()
                        Text = text_cleaning(raw)
                        Text = symbol_cleaning(Text)
                    break

            # only append if we got all three
            if Speaker and Voice and Text:
                results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})

PROCESSORS = {
    0:   process_type0,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.ws2.src", recursive=True)

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