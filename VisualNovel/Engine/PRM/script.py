import re
import json
import argparse
from tqdm import tqdm
from glob import glob

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

def load_lines(path):
    with open(path, 'r', encoding='cp932') as f:
        lines = f.readlines()
    return lines

def process_type0(lines, results):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 查找 SoundPlay 行
        sound_match = re.match(r'<SoundPlay\s+\d+,(.+?)>', line)
        if not sound_match:
            i += 1
            continue
            
        voice_file = sound_match.group(1)
        
        # 查找下一行的角色名
        i += 1
        if i >= len(lines):
            break
            
        speaker_line = lines[i].strip()
        speaker_match = re.match(r'【(.+?)】', speaker_line)
        if not speaker_match:
            continue
            
        speaker = speaker_match.group(1)
        
        # 收集对话文本，直到遇到 <KW><WinClear>
        text_lines = []
        i += 1
        while i < len(lines):
            current_line = lines[i].strip()
            if not current_line:
                i += 1
                continue
                
            text_lines.append(current_line)
            
            # 如果这行包含 <KW><WinClear>，收集完毕
            if '<KW><WinClear>' in current_line:
                i += 1
                break
                
            i += 1
        
        # 处理收集到的文本
        if text_lines:
            full_text = ''.join(text_lines)
            # 移除 <KW><WinClear> 标记
            full_text = re.sub(r'<KW><WinClear>', '', full_text)
            cleaned_text = text_cleaning(full_text)
            
            if cleaned_text:  # 只添加非空文本
                results.append({
                    "Speaker": speaker.replace('・', ''),
                    "Voice": voice_file.replace('.ogg', ''),
                    "Text": cleaned_text
                })

PROCESSORS = {
    0:   process_type0,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.txt", recursive=True)

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