import re
from .text_cleaning import text_cleaning_02

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
