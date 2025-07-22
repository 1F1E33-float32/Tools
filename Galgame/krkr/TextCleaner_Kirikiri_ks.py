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
    p.add_argument("-ft", type=float, default=0.2)
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

'''
@Talk name=いつみ voice=ITM000020
「やっぱり昨日渋丘スタジオにいたのって、
　永倉くんだったんだ。そっか、かなめさんのお手伝いで……」
'''
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
[cn name="深青" voice="mio_0089"]
「ひ……！　……ん……おい、邪魔すんなハゲ。こっちは遊びでやってんじゃねーんだよ。キルレート下がったらどうすんだ」
[en]
'''
def process_type0_1(lines, results):
    cn_re = re.compile(r'\[cn\s+name="([^"]+)"(?:\s+voice="([^"]+)")?\]')
    for i, line in enumerate(lines):
        m = cn_re.search(line)
        if not m:
            continue

        Speaker = m.group(1).replace('　', '')
        Voice   = m.group(2) if m.group(2) else None

        tmp = []
        # gather all lines until we hit the [en] tag
        for j in range(i + 1, len(lines)):
            if lines[j].strip().startswith('[en]'):
                Text = text_cleaning_02(''.join(tmp))
                results.append({
                    "Speaker": Speaker,
                    "Voice":   Voice,
                    "Text":    Text
                })
                break
            tmp.append(lines[j])

'''
[Voice file=RAMUNE_0B_1425] 
[Talk name=美咲]
「はぁ、はぁはぁ、お待たせっ！／
大丈夫なの、カナちゃん！？」
[Hitret]
'''
def process_type0_2(lines, results):
    """
    只处理以下格式：
      [Voice file=XXX]
      [Talk name=YYY]
      对话内容...
      [Hitret]
    """
    current_voice = None

    for i, line in enumerate(lines):
        # 捕获 [Voice file=...] 并缓存 voice 名称
        m_voice = re.search(r'\[Voice\s+file=([^\]\s]+)\]', line)
        if m_voice:
            current_voice = m_voice.group(1).split('/')[0]
            continue

        # 只识别 [Talk name=...] 格式
        m_talk = re.search(r'\[Talk\s+name=([^\]\s]+)\]', line)
        if not m_talk:
            continue

        Speaker = m_talk.group(1).split('/')[0]
        Voice   = current_voice

        # 收集 Talk 之后到 [Hitret] 之前的所有行
        tmp = []
        for j in range(i + 1, len(lines)):
            if lines[j].startswith('[Hitret]'):
                Text = text_cleaning_02(''.join(tmp))
                results.append({
                    "Speaker": Speaker,
                    "Voice": Voice,
                    "Text": Text
                })
                break
            tmp.append(lines[j])

        # 用过一次 voice 就重置，防止误用到下一段
        current_voice = None

'''
@nm t="臨" s=rin_0015
「んー、特には何も。[r]
　そっちが寂しいかなーって思ってさ」[np]
'''
def process_type1(lines, results):
    header_re = re.compile(r'@nm\s+t="([^"]+)"\s+s=([^\s]+)')
    i = 0
    while i < len(lines):
        line = lines[i]
        m = header_re.match(line)
        if not m:
            i += 1
            continue

        # 解析说话人和声音
        speaker = m.group(1)
        voice   = m.group(2)

        # 累积文本，直到遇到 [np]
        tmp = []
        i += 1
        while i < len(lines):
            text_line = lines[i]
            tmp.append(text_line)
            if '[np]' in text_line:
                break
            i += 1

        text = ''.join(tmp)
        text = text_cleaning_02(text)

        results.append({
            "Speaker": speaker,
            "Voice": voice,
            "Text": text
        })

        i += 1

'''
[天使 vo=vo1_0001 text="？？？"]
[>>]いや惚れろよ、このビューチーな私に[<<][c]
'''
def process_type2(lines, results):
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

'''
[msgname name=IWATANI]
[cv str=i075]
「ま、そりゃそうだわな。誰だって、結局は自分の身がかわいいもんな」
[np][cm]
'''
def process_type3(lines, results):
    speaker = None
    voice   = None
    buffer  = []

    for line in lines:
        # 1) detect speaker
        m_name = re.search(r'\[msgname\s+name=([^\]]+)\]', line)
        if m_name:
            speaker = m_name.group(1)
            buffer.clear()
            continue

        # 2) detect voice
        m_cv = re.search(r'\[cv\s+str=([^\]]+)\]', line)
        if m_cv and speaker is not None:
            voice = m_cv.group(1)
            continue

        # 3) accumulate text until the end marker
        if speaker is not None:
            # end of block
            if line.startswith('[np]') and '[cm]' in line:
                raw_text = ''.join(buffer).strip()
                Text = text_cleaning_02(raw_text)
                results.append({
                    "Speaker": speaker,
                    "Voice":   voice,
                    "Text":    Text
                })
                # reset for next block
                speaker = None
                voice   = None
                buffer.clear()
            else:
                buffer.append(line)

    return results

'''
@Voice
【Speaker】
Text

@Voice sketch
@【Speakerスケブ】 制服２ 正面 スケブ 通常 奥 中
@スケブ text="Text"

@Speaker voice=Voice
【Speaker】
Text
'''
def process_type4(lines, results):
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # —— 形式 3: @Speaker voice=Voice
        mC = re.match(r'^@(?P<Speaker>[^\s]+)\s+voice=(?P<Voice>[^\s]+)$', line)
        if mC:
            speaker = mC.group('Speaker')
            voice   = mC.group('Voice')
            # 下行应该是 【Speaker】
            if i + 1 < len(lines):
                mS = re.match(r'^【(?P<SPEAK>[^\]]+)】$', lines[i+1].strip())
                if mS:
                    # 再下一行就是 Text
                    text = lines[i + 2]
                    results.append({
                        "Speaker": speaker.split('/')[0],
                        "Voice":   voice,
                        "Text":    text_cleaning_02(text.replace('/', ''))
                    })
                    i += 3
                    continue

        # —— 形式 2: @Voice sketch
        mB = re.match(r'^@(?P<Voice>[^\s]+)\s+\w+$', line)
        if mB and 'sketch' in line:
            voice = mB.group('Voice')
            # 下行形如 @【Speakerスケブ】
            if i + 1 < len(lines):
                mSB = re.match(r'^@【(?P<Speaker>[^】]+)】', lines[i+1])
                if mSB:
                    speaker = mSB.group('Speaker')
                    # 再下一行形如 @スケブ text="Text"
                    if i + 2 < len(lines):
                        mT = re.match(r'^@\S+\s+text="(?P<Text>.*)"', lines[i+2])
                        if mT:
                            text = mT.group('Text')
                            results.append({
                                "Speaker": speaker.split('/')[0],
                                "Voice":   voice,
                                "Text":    text_cleaning_02(text.replace('/', ''))
                            })
                            i += 3
                            continue

        # —— 形式 1: @Voice
        mA = re.match(r'^@(?P<Voice>[^\s]+)$', line)
        if mA:
            voice = mA.group('Voice')
            # 下行应该是 【Speaker】
            if i + 1 < len(lines):
                mS = re.match(r'^【(?P<Speaker>[^】]+)】$', lines[i+1].strip())
                if mS:
                    speaker = mS.group('Speaker')
                    # 再下一行就是 Text
                    text = lines[i + 2]
                    results.append({
                        "Speaker": speaker.split('/')[0],
                        "Voice":   voice,
                        "Text":    text_cleaning_02(text.replace('/', ''))
                    })
                    i += 3
                    continue
        i += 1

    return results

"""
@v s=VOICE
（中间可能有 @se、@flash、@cut 等指令）
@【Speaker】
台词行1
台词行2
"""
def process_type5(lines, results):
    voice_re   = re.compile(r'^@v\s+s=(\S+)')
    speaker_re = re.compile(r'^@【(.+?)】')

    i = 0
    n = len(lines)
    while i < n:
        # 1. 匹配到 voice 标记
        m_v = voice_re.match(lines[i])
        if not m_v:
            i += 1
            continue
        voice = m_v.group(1)
        j = i + 1

        # 2. 在同一段落中继续寻找 speaker 或新的 voice
        while j < n:
            # 如果在找到台词前就遇到下一个 voice，则放弃当前 voice，跳到新 voice
            if voice_re.match(lines[j]):
                break

            # 找到 speaker 行
            m_sp = speaker_re.match(lines[j])
            if m_sp:
                speaker = m_sp.group(1)
                # 3. 收集后续所有非 @ 开头的台词行
                text_lines = []
                k = j + 1
                while k < n and not lines[k].startswith('@'):
                    text_lines.append(lines[k].strip())
                    k += 1
                text = text_cleaning_02(''.join(text_lines))
                results.append({
                    "Voice": 'cv' + voice,
                    "Speaker": speaker,
                    "Text": text
                })
                j = k
                break
            j += 1
        i = j

'''
@満花 voice=C01_いもうと２_エンド01_0027.ogg
【満花】　「あっあっあっ、あああん、気持ちいい……」
'''
def process_type6(lines, results):
    current_speaker = None
    current_voice   = ""

    header_re = re.compile(r'^@(?P<Speaker>\S+)\s+voice=(?P<Voice>\S+)')
    text_re   = re.compile(r'^【.*?】　「?(?P<Text>.+?)」?$')

    for line in lines:
        m1 = header_re.match(line)
        if m1:
            current_speaker = m1.group('Speaker')
            current_voice   = m1.group('Voice').split('.')[0]
            continue

        if current_speaker is not None:
            m2 = text_re.match(line)
            if m2:
                raw_text = m2.group('Text').strip()
                cleaned  = text_cleaning_02(raw_text)
                results.append({
                    "Speaker": current_speaker,
                    "Voice":   current_voice,
                    "Text":    cleaned
                })

'''
[菜穂子 voice=D10750]
【菜穂子】
「公序良俗に反した行いがなければ、止め立てする理由は
　私たちにはないということ」
'''
def process_type7(lines, results):
    header_re = re.compile(r'^\[([^\s\]]+)\s+voice=([^\]\s]+)')
    
    while lines:
        line = lines[0].strip()
        m = header_re.match(line)
        if not m:
            lines.pop(0)
            continue

        speaker = m.group(1)
        voice   = m.group(2)
        lines.pop(0)

        if lines and lines[0].strip().startswith('【') and lines[0].strip().endswith('】'):
            lines.pop(0)

        text_lines = []
        while lines:
            ln = lines[0]
            if ln == '':
                lines.pop(0)
                break
            text_lines.append(ln)
            lines.pop(0)
        text_lines = ''.join(text_lines)
        text_lines = text_cleaning_02(text_lines)

        results.append({
            "Speaker": speaker,
            "Voice":   voice,
            "Text":    text_lines
        })
PROCESSORS = {
    0:   process_type0,
    0.1: process_type0_1,
    0.2: process_type0_2,
    1:   process_type1,
    2:   process_type2,
    3:   process_type3,
    4:   process_type4,
    5:   process_type5,
    6:   process_type6,
    7:   process_type7,
}

def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = (glob(f"{JA_dir}/**/*.ks", recursive=True) + glob(f"{JA_dir}/**/*.txt", recursive=True) + glob(f"{JA_dir}/**/*.scn", recursive=True))

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