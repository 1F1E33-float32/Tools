import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\scenario")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-ft", type=int, default=0)
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r"\[.*?,(.*?),.*?\]", r"\1", text)
    text = text.replace('」', '').replace('「', '').replace('（', '').replace('）', '').replace('『', '').replace('』', '')
    text = text.replace('〈ハ〉', '').replace('　', '').replace('\n', '')
    return text

def load_lines(path):
    with open(path, 'r', encoding='cp932') as f:
        lines = f.readlines()
    return [ln.lstrip() for ln in lines if not (ln.lstrip().startswith('^') or ln.lstrip().startswith('\\') or ln.lstrip().startswith('//'))]

def process_type0(lines, results):
    for line in lines:
        line = line.strip()
        if not line:
            continue

        line = re.sub(r'\[rb,([^,]+?),[^,]+?\]', r'\1', line)
        pattern = re.compile(
            r'^\s*'
            r'(?P<voice>(?!none$)[^,]+)\s*,\s*'
            r'(?P<speaker>[^,]+)\s*,\s*'
            r'(?P<text>.+?)\s*$',
            flags=re.IGNORECASE
        )
        m = pattern.match(line)
        if not m:
            continue

        voice   = m.group('voice').strip()
        speaker = m.group('speaker').strip()
        speaker = speaker.split('＠')[0]
        speaker = speaker.replace('【', '').replace('】', '')
        text    = m.group('text').strip()

        cleaned = text_cleaning(text)
        results.append({
            "Speaker": speaker,
            "Voice": voice,
            "Text": cleaned
        })

'''
％nat_k1_01_04_016
【ナツ】
「おーなるほど。それでシャワーを浴びて」
'''
def process_type1(lines, results):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('％'):
            # 1) Voice: everything after '%'
            voice = line[1:].strip()

            # 2) Speaker: next line, inside 【…】
            i += 1
            if i < len(lines):
                sp_line = lines[i].strip()
                speaker_raw = sp_line.strip('【】')
                speaker = speaker_raw.split('＠')[-1]
            else:
                speaker = ''

            # 3) Text: next line, taken raw
            i += 1
            if i < len(lines):
                text_line = text_cleaning(lines[i])

                results.append({
                    "Speaker": speaker,
                    "Voice": voice,
                    "Text": text_line
                })

        i += 1

PROCESSORS = {
    0:   process_type0,
    1:   process_type1,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.s", recursive=True)

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