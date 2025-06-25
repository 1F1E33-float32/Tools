import re
import json
import chardet
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\scenario")
    p.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    p.add_argument("-ft", type=float, default=1)
    return p.parse_args(args=args, namespace=namespace)

def text_cleaning_01(text):
    text = text.replace('\n', '')
    text = re.sub(r"\[([^\]]+?)'[^]]+\]", r'\1', text)
    text = re.sub(r"\['([^']+?) text=\"[^\"]+?\"\]", r"\1", text)
    text = re.sub(r"＃\([^()]+\) ", "", text)
    text = text.replace('[r]', '').replace('[np]', '')
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '')
    text = re.sub(r"\[[^\]]*\]", '', text)
    text = text.replace('"', '')
    return text

def text_cleaning_02(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '').replace('\n', '')
    text = text.replace('　', '').replace('／', '')
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
    return [ln.lstrip() for ln in lines if not ln.lstrip().startswith(';')]

def process_type0(lines, results):
    for i, line in enumerate(lines):
        m = re.search(r'@Talk\s+name=([^\s]+)(?:\s+voice=([^\s]+))?', line)
        if not m:
            continue
        Speaker = m.group(1).split('/')[0]
        Voice   = m.group(2).split('/')[0] if m.group(2) else None
        tmp = []
        for j in range(i + 1, len(lines)):
            if lines[j].startswith('@Hitret'):
                Text = text_cleaning_02(''.join(tmp))
                results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
                break
            tmp.append(lines[j])

'''
[天使 vo=vo1_0001 text="？？？"]
[>>]いや惚れろよ、このビューチーな私に[<<][c]
'''
def process_type1(lines, results):
    speaker_re = re.compile(r'\[(?P<Speaker>[^\s]+)\s+vo=(?P<Voice>\S+)[^\]]*\]')
    text_re    = re.compile(r'\[>>\](?P<Text>.*?)\[<<\]\[c\]')
    current = {}
    for i, line in enumerate(lines):
        m1 = speaker_re.search(line)
        if m1:
            current['Speaker'] = m1.group('Speaker')
            current['Voice']   = m1.group('Voice')
            continue

        m2 = text_re.search(line)
        if m2 and 'Speaker' in current:
            results.append({
                "Speaker": current['Speaker'],
                "Voice":   current['Voice'],
                "Text":    text_cleaning_02(m2.group('Text').strip())
            })
            current.clear()
    return results

PROCESSORS = {
    0:   process_type0,
    1:   process_type1,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = (glob(f"{JA_dir}/**/*.ks", recursive=True) + glob(f"{JA_dir}/**/*.txt", recursive=True) + glob(f"{JA_dir}/**/*.ms", recursive=True))

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