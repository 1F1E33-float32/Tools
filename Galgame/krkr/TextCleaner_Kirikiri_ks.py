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
    p.add_argument("-ft", type=float, default=2)
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
    """读取脚本并去掉行首注释(;)"""
    try:
        with open(path, 'r', encoding=guess_encoding(path)) as f:
            lines = f.readlines()
    except (UnicodeDecodeError, TypeError):
        with open(path, 'r', encoding='cp932') as f:
            lines = f.readlines()
    # lstrip(): 某些脚本前面可能有空格
    return [ln.lstrip() for ln in lines if not ln.lstrip().startswith(';')]

# ---------- 各种解析函数 ----------
def process_type0(filename, lines, results):
    for i, line in enumerate(lines):
        if 'rt=' in line:
            m = re.findall(r'@nm\s+t="([^"]*)"\s+rt="([^"]*)"\s+s=(.*)$', line)
            if not m:
                continue
            Speaker, Voice = m[0][1], m[0][2].split("/")[-1]
            skip, tmp = False, []
            for j in range(i + 1, len(lines)):
                if lines[j].startswith(';'):
                    print(f"\nWarning: {filename} {lines[j]}")
                    skip = True
                    break
                if "[np]" in lines[j]:
                    tmp.append(lines[j])
                    break
                if "[r]" in lines[j]:
                    tmp.append(lines[j])
            if not skip:
                Text = text_cleaning_01(''.join(tmp))
                results.append((Speaker, Voice, Text))
        else:
            m = re.findall(r'@nm\s+t="([^"]+)"\s+s=([^\s"]+)', line)
            if not m:
                continue
            Speaker, Voice = m[0][0], m[0][1].split("/")[-1]
            skip, tmp = False, []
            for j in range(i + 1, len(lines)):
                if lines[j].startswith(';') and not lines[j].startswith(';//'):
                    print(f"\nWarning: {filename} {lines[j]}")
                    skip = True
                    break
                if "[np]" in lines[j]:
                    tmp.append(lines[j])
                    break
                if "[r]" in lines[j]:
                    tmp.append(lines[j])
            if not skip:
                Text = text_cleaning_01(''.join(tmp))
                results.append((Speaker, Voice, Text))

def process_type1(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.findall(r'\[([^\s\]]+)\s+vo=["]?([^"\s\]]+)["]?', line)
        if m:
            Speaker, Voice = m[0]
            Text = text_cleaning_02(lines[i + 1])
            results.append((Speaker, Voice, Text))

def process_type2(filename, lines, results):
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
                results.append((Speaker, Voice, Text))
                break
            tmp.append(lines[j])

def process_type3(filename, lines, results):
    for i, line in enumerate(lines):
        m1 = re.findall(r'[;@]?@(\S+)\s+voice="([^"]+)"', line)
        if not m1:
            continue
        Speaker, Voice = m1[0]
        Speaker = Speaker.split('/')[0]
        Voice = Voice.lower()
        m2 = re.findall(r'[;]?\s*【[^】]+】(.+)', lines[i + 1])
        if m2:
            Text = text_cleaning_02(m2[0])
            results.append((Speaker, Voice, Text))
        elif i + 2 < len(lines) and lines[i + 2].startswith('['):
            Text = text_cleaning_02(lines[i + 1])
            results.append((Speaker, Voice, Text))

def process_type3_5(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.findall(r'@(\S+)\s+voice=([^"]+)', line)
        if not m:
            continue
        Speaker, Voice = m[0][0], m[0][1].lower()
        if '【' in lines[i + 1] and '】' in lines[i + 1]:
            Text = text_cleaning_02(lines[i + 2])
            if '【ゆり】' in Text:  # 原逻辑保留
                pass
            results.append((Speaker, Voice, Text))

def process_type4(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.findall(r'\[(.*?)\s+voice="(.*?)"\]', line)
        if m:
            Speaker, Voice = m[0][0], m[0][1]
            Text = text_cleaning_02(lines[i + 2])
            results.append((Speaker, Voice, Text))

def process_type5(filename, lines, results):
    for i, line in enumerate(lines):
        m1 = re.search(r'\[Voice\s+file=([^\s]+)\s+id=([^\]]+)\]', line)
        tmp_voice = []
        if m1:
            tmp_voice.append(m1.group(1))
            for j in range(i + 1, len(lines)):
                m2 = re.search(r'\[Voice\s+file=([^\s]+)\s+id=([^\]]+)\]', lines[j])
                m3 = re.search(r'\[Talk\s+name=([^\]]+)\]', lines[j])
                if m2:
                    tmp_voice.append(m2.group(1))
                elif m3:
                    speakers = re.split(r"[＆&]", m3.group(1))
                    tmp = []
                    for n in range(j + 1, len(lines)):
                        if '[Hitret]' in lines[n]:
                            Text = text_cleaning_01(''.join(tmp))
                            for Voice, Speaker in zip(tmp_voice, speakers):
                                results.append((Speaker, Voice, Text))
                            break
                        tmp.append(lines[n])
                    break
            continue  # 进入下一行

        m4 = re.search(r'\[Voice\s+file=([^\]]+)\]', line)
        if m4:
            Voice = m4.group(1)
            for j in range(i + 1, len(lines)):
                m5 = re.search(r'\[Talk\s+name=([^\]]+)\]', lines[j])
                if m5:
                    Speaker = m5.group(1)
                    tmp = []
                    for n in range(j + 1, len(lines)):
                        if '[Hitret]' in lines[n]:
                            Text = text_cleaning_01(''.join(tmp))
                            results.append((Speaker, Voice, Text))
                            break
                        tmp.append(lines[n])
                    break

def process_type6(filename, lines, results):
    for i, line in enumerate(lines):
        m1 = re.search(r'\[Voice\s+file=([^\]]+)\]', line)
        if not m1:
            continue
        Voice = m1.group(1)
        for j in range(i + 1, len(lines)):
            m2 = re.search(r'\[Talk\s+name=([^\]]+)\]', lines[j])
            if m2:
                Speaker = m2.group(1)
                tmp = []
                for k in range(j + 1, len(lines)):
                    if "[r]" in lines[k]:
                        tmp.append(lines[k])
                    else:
                        tmp.append(lines[k])
                        Text = text_cleaning_01(''.join(tmp))
                        results.append((Speaker, Voice, Text))
                        break
                break

def process_type7(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.findall(r"@hbutton.*?\['storage'\s*=>\s*'([^']+)']", line)
        if not m:
            continue
        path = m[0]
        Speaker = path.split('/')[2]
        Voice   = path.split('/')[3]
        tmp = []
        for j in range(i + 1, len(lines)):
            if '[endvoice]' in lines[j] or (lines[j].startswith("@") and tmp):
                Text = text_cleaning_01(''.join(tmp))
                results.append((Speaker, Voice, Text))
                break
            elif "@" in lines[j]:
                continue
            tmp.append(lines[j])

def process_type7_5(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.findall(r'\[voice_([^\s\]]+)\s+storage="([^"]+)"\]', line)
        if not m:
            continue
        Speaker, Voice = m[0][0], m[0][1].split('.')[0]
        for j in range(i + 1, len(lines)):
            if '[opacity_indent]' in lines[j] and '[endindent]' in lines[j]:
                Text = text_cleaning_01(lines[j])
                results.append((Speaker, Voice, Text))
                break

def process_type8(filename, lines, results):
    for i, line in enumerate(lines):
        m1 = re.findall(r'\[ps\s+n=([^\s]+)\s+v="([^"]+)"\]', line)
        if not m1:
            continue
        Speaker = m1[0][0].split('/')[0]
        Voice   = m1[0][1]
        tmp, is_text = [], False
        for j in range(i + 1, len(lines)):
            if "[else]" in lines[j]:
                is_text = True
            elif "[endif]" in lines[j]:
                Text = text_cleaning_01(''.join(tmp))
                results.append((Speaker, Voice, Text))
                break
            elif is_text:
                tmp.append(lines[j])

def process_type8_5(filename, lines, results):
    for i, line in enumerate(lines):
        m1 = re.findall(r'\[pv\s+char="([^"]+)"\s+voice=([^\s\]]+)', line)
        if not m1:
            continue
        Speaker = m1[0][0].split('/')[0]
        Voice   = m1[0][1].replace('.ogg', '')
        # 收集到下一 [ps]
        dialogue = []
        j = i + 1
        while j < len(lines) and '[ps]' not in lines[j]:
            dialogue.append(lines[j])
            j += 1
        if j < len(lines) and '[ps]' in lines[j]:
            dialogue.append(lines[j])
        m2 = re.search(r'「(.*?)」', ''.join(dialogue), re.DOTALL)
        if m2:
            Text = text_cleaning_01(m2.group(1))
            if Text:
                results.append((Speaker, Voice, Text))

def process_type9(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.findall(r'\[mess[^\]]*?name=([^\s\]]+)[^\]]*?voice="([^"]+)"', line)
        if not m:
            continue
        Speaker = m[0][0].split("／")[0]
        Voice   = m[0][1]
        tmp = []
        for j in range(i + 1, len(lines)):
            if "[p2]" in lines[j]:
                break
            tmp.append(lines[j].replace("[r]", ""))
        Text = text_cleaning_01(''.join(tmp))
        results.append((Speaker, Voice, Text))

def process_type10(filename, lines, results):
    for i, line in enumerate(lines):
        m = re.search(r'\[([^ \]]+).*?\bvo=([^\s\]]+)', line)
        if not m:
            continue
        Speaker = m.group(1).split("／")[0]
        Voice = m.group(2)
        if i + 1 >= len(lines):
            continue
        text_line = lines[i + 1]
        m2 = re.search(r'\[>>\](.*?)\[<<\]\[c\]', text_line)
        if m2:
            Text = text_cleaning_01(m2.group(1))
            results.append((Speaker, Voice, Text))

# ---------- 分派表 ----------
PROCESSORS = {
    0:   process_type0,
    1:   process_type1,
    2:   process_type2,
    3:   process_type3,
    3.5: process_type3_5,
    4:   process_type4,
    5:   process_type5,
    6:   process_type6,
    7:   process_type7,
    7.5: process_type7_5,
    8:   process_type8,
    8.5: process_type8_5,
    9:   process_type9,
    10:  process_type10,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    # 收集所有脚本
    filelist = (glob(f"{JA_dir}/**/*.ks", recursive=True) +
                glob(f"{JA_dir}/**/*.txt", recursive=True) +
                glob(f"{JA_dir}/**/*.ms", recursive=True))

    results = []             # 最终结果
    scene   = 0              # 文件计数（从 1 开始）

    for fn in tqdm(filelist, desc="Parsing"):
        lines = load_lines(fn)

        file_results = []    # 该脚本产生的若干条记录
        processor(fn, lines, file_results)

        if not file_results:
            continue

        scene += 1           # 处理完一个文件，scene+1
        for line_idx, (Speaker, Voice, Text) in enumerate(file_results, start=1):
            results.append({
                'Speaker': Speaker,
                'Voice':   Voice,
                'Text':    Text,
                'scene':  scene,
                'line':   line_idx,
            })

    # 写出 JSON
    with open(op_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op, args.ft)