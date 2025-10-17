import re
import json
import chardet
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    p.add_argument("-op", type=str, default=r'D:\Fuck_VN\index.json')
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
    return [ln.lstrip() for ln in lines if not ln.startswith('#')]


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

def process_type1(lines, results):
    current_voice   = None
    current_speaker = None
    in_quote        = False
    quote_buf       = []

    for line in lines:
        # 1) 语音轨
        voice_m = re.search(r'cvon\s*\(\s*"([^"]+)"\s*\)', line)
        if voice_m:
            current_voice = voice_m.group(1)
            continue

        # 2) 纯说话人一行（如：[男性アナウンサー]）
        spk_line_m = re.search(r'^\s*\[([^\]]+)\]\s*$', line)
        if spk_line_m:
            current_speaker = spk_line_m.group(1)
            continue

        # 3) 台词区块
        if not in_quote:
            if '「' in line:
                in_quote = True
                after_open = line.split('「', 1)[1]
                # 如果本行就闭合
                if '」' in after_open:
                    raw_text = after_open.split('」', 1)[0]
                    raw_text = re.sub(r'^[\s\u3000]+', '', raw_text, flags=re.MULTILINE)
                    text = text_cleaning(raw_text)
                    if text and current_voice and current_speaker:
                        results.append({
                            "Speaker": current_speaker,
                            "Voice":   current_voice,
                            "Text":    text
                        })
                    current_speaker = None
                    in_quote = False
                else:
                    quote_buf = [after_open]
        else:
            if '」' in line:
                before_close = line.split('」', 1)[0]
                quote_buf.append(before_close)
                raw_text = '\n'.join(quote_buf)
                raw_text = re.sub(r'^[\s\u3000]+', '', raw_text, flags=re.MULTILINE)
                text = text_cleaning(raw_text)
                if text and current_voice and current_speaker:
                    results.append({
                        "Speaker": current_speaker,
                        "Voice":   current_voice,
                        "Text":    text
                    })
                current_speaker = None
                in_quote  = False
                quote_buf = []
            else:
                quote_buf.append(line)

PROCESSORS = {
    0:   process_type0,
    1:   process_type1,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.scr", recursive=True)

    results = []
    for fn in tqdm(filelist, ncols=150):
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