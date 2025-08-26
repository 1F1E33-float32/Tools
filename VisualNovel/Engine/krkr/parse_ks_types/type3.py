import re
from .text_cleaning import text_cleaning_02

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
        m_name = re.search(r'\[msgname\s+name=([^\]]+)\]', line)
        if m_name:
            speaker = m_name.group(1)
            buffer.clear()
            continue

        m_cv = re.search(r'\[cv\s+str=([^\]]+)\]', line)
        if m_cv and speaker is not None:
            voice = m_cv.group(1)
            continue

        if speaker is not None:
            if line.startswith('[np]') and '[cm]' in line:
                raw_text = ''.join(buffer).strip()
                Text = text_cleaning_02(raw_text)
                results.append({
                    "Speaker": speaker,
                    "Voice":   voice,
                    "Text":    Text
                })
                speaker = None
                voice   = None
                buffer.clear()
            else:
                buffer.append(line)

    return results

'''
[name text=ステラ]
[voice storage="cv_D00061"]
「あ……アベスターグの支部。[r]
　お兄ちゃん、せっかくだし寄っていかない？」
'''
def process_type3_1(lines, results):
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        m_name = re.match(r'^\[name\s+text=([^\]]+)\]', line)
        if not m_name:
            i += 1
            continue

        speaker = m_name.group(1)
        voice = None

        i += 1
        while i < n:
            m_voice = re.match(r'^\[voice\s+storage="([^"]+)"\]', lines[i].strip())
            if m_voice:
                voice = m_voice.group(1)
                i += 1
                break
            i += 1

        if voice is None:
            continue

        buf = []
        while i < n and not lines[i].startswith('['):
            buf.append(lines[i])
            i += 1

        raw_text = ''.join(buf).replace('[r]', '\n').strip()

        Text = text_cleaning_02(raw_text)

        results.append({
            "Speaker": speaker,
            "Voice":   voice,
            "Text":    Text
        })
    return results
