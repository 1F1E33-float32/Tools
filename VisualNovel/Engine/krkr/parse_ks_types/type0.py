import re
from .text_cleaning import text_cleaning_02

'''
@Talk name=いつみ voice=ITM000020
「やっぱり昨日渋丘スタジオにいたのって、
　永倉くんだったんだ。そっか、かなめさんのお手伝いで……」


@talk voice=Annna_00000 name=杏奈
そんな訳ないでしょう。
@hitret
'''
def process_type0(lines, results):
    i = 0
    while i < len(lines):
        line = lines[i]

        if re.search(r'^\s*@talk\b', line, flags=re.IGNORECASE):
            attrs = dict((k.lower(), v.split('/')[0]) for k, v in re.findall(r'\b(name|voice)=([^\s]+)', line, flags=re.IGNORECASE))

            Speaker = attrs.get('name') or None
            Voice   = attrs.get('voice') or None

            tmp = []
            i += 1
            while i < len(lines):
                if re.match(r'^\s*@hitret\b', lines[i], flags=re.IGNORECASE):
                    Text = text_cleaning_02(''.join(tmp))
                    results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
                    break
                tmp.append(lines[i])
                i += 1

            else:
                Text = text_cleaning_02(''.join(tmp))
                results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
                return
        i += 1


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
[Voice file=RAMUNE_0B_1425
[Talk name=美咲]
「はぁ、はぁはぁ、お待たせっ！／
大丈夫なの、カナちゃん！？」
[Hitret
'''
def process_type0_2(lines, results):
    current_voice = None

    for i, line in enumerate(lines):
        m_voice = re.search(r'(?i)\[Voice\s+file="?([^\]\s"]+)"?', line)
        if m_voice:
            current_voice = m_voice.group(1).split('/')[0]
            continue

        m_talk  = re.search(r'(?i)\[Talk\s+name="?([^\]\s"]+)"?\]',  line)
        if not m_talk:
            continue

        Speaker = m_talk.group(1).split('/')[0]
        Voice   = current_voice

        tmp = []
        for j in range(i + 1, len(lines)):
            if lines[j].lower().startswith('[hitret'):
                Text = text_cleaning_02(''.join(tmp))
                results.append({
                    "Speaker": Speaker,
                    "Voice": Voice,
                    "Text": Text
                })
                break
            tmp.append(lines[j])

        current_voice = None

'''
[【小鳥】][voia v="koto_0203_001"]
「うん、いーよ。えーっと？　穴埋めかあ」[ver]

[【小鳥】][voia v="koto_0203_002"]
「うんうん、そーだね。これはねえ、[r]
　"Ｉｔ"の後に、過去進行形が来るんだよ。[r]
　だから、正解は４番」[ver]
'''
def process_type0_3(lines, results):
    speaker_re = re.compile(r'\[【([^】]+)】\]')
    voice_re = re.compile(r'\[\w{4}\s+v="([^"]+)"\]')
    
    i = 0
    n = len(lines)
    
    while i < n:
        line = lines[i].strip()
        
        # 查找 Speaker
        m_speaker = speaker_re.search(line)
        if not m_speaker:
            i += 1
            continue
            
        speaker = m_speaker.group(1)
        
        # 在同一行查找 Voice
        m_voice = voice_re.search(line)
        if not m_voice:
            i += 1
            continue
            
        voice = m_voice.group(1)
        
        # 收集文本直到遇到 [ver]
        i += 1
        text_lines = []
        while i < n:
            if '[ver]' in lines[i]:
                # 包含 [ver] 的行，取 [ver] 之前的部分
                text_before_ver = lines[i].split('[ver]')[0]
                if text_before_ver.strip():
                    text_lines.append(text_before_ver)
                i += 1
                break
            text_lines.append(lines[i])
            i += 1
            
        if text_lines:
            text = text_cleaning_02(''.join(text_lines))
            results.append({
                "Speaker": speaker,
                "Voice": voice,
                "Text": text
            })

'''
[nm t="執事" rt="翠碕" s=aax_0011]「"[gly t="デビルズ・オーガン"][rb t="悪魔の臓器|デビルズ・オーガン"][egly]"の中でも、極めて特殊な部類に入る能力です」[wvl]
[nm t="睦月" s=mut_0187]「さてな」[np]
'''
def process_type0_4(lines, results):
    nm_re = re.compile(r'\[nm\s+t="([^"]+)"(?:\s+rt="[^"]*")?\s+s=([^\]]+)\]')
    
    for line in lines:
        m = nm_re.search(line)
        if not m:
            continue
            
        Speaker = m.group(1)
        Voice = m.group(2)
        
        # 获取标签后的文本内容
        text_content = line[m.end():]
        
        if text_content.strip():
            Text = text_cleaning_02(text_content)
            results.append({
                "Speaker": Speaker,
                "Voice": Voice,
                "Text": Text
            })