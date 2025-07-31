import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\ks")
    p.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    p.add_argument("-ft", type=float, default=0)
    return p.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace('／', '').replace('\n', '')
    return text

def load_lines(path):
    with open(path, 'r', encoding='cp932') as f:
        lines = f.readlines()
    return [ln.lstrip() for ln in lines if not ln.lstrip().startswith(';')]

def process_type0(lines, results):
    msg_re = re.compile(r'\[MESSAGE\s+NAME="(?P<speaker>[^"]+)"\s+VOICE="(?P<voice>[^"]+)"(?:\s+ICON="[^"]*")?\]')
    for i, line in enumerate(lines):
        m = msg_re.search(line)
        if not m:
            continue

        Speaker = m.group('speaker')
        Voice   = m.group('voice')
        tmp     = []

        for j in range(i+1, len(lines)):
            if lines[j].strip() == '[/MESSAGE]':
                Text = text_cleaning(''.join(tmp))
                results.append({
                    "Speaker": Speaker,
                    "Voice": Voice.replace('.wav', ''),
                    "Text": Text
                })
                break

            tmp.append(lines[j])

PROCESSORS = {
    0:   process_type0
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.ks", recursive=True)

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