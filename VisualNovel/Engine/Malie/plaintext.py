import re
import json
import chardet
import argparse

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\_maliescenario.ms")
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
    for line in lines:
        speaker_m = re.search(r'MALIE_NAME\("([^"]+)"\)', line)
        voice_m   = re.search(r'_voice\("([^"]+)"\)', line)
        if not speaker_m or not voice_m:
            continue

        speaker = speaker_m.group(1)
        voice   = voice_m.group(1)

        segments = re.findall(r'\$"([^"]*)"', line)

        text_parts = [seg for seg in segments if not re.search(r'\\', seg) and seg not in ['「', '」']]

        text = text_cleaning(''.join(text_parts))

        if text:
            results.append({
                "Speaker": speaker,
                "Voice":    voice,
                "Text":     text
            })
PROCESSORS = {
    0:   process_type0,
}

def main(JA_file, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    results = []
    lines = load_lines(JA_file)

    processor(lines, results)

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