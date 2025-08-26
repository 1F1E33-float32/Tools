import re
from .text_cleaning import text_cleaning_02

'''
@nm t="臨" s=rin_0015
「んー、特には何も。[r]
　そっちが寂しいかなーって思ってさ」[np]

@saudio t="詩乃" fv=shi_0056 front="「わ、わかりました」" bv=shu_0024 back="「あとで観るのっ！？　そんなの、は、恥ずかしい……」"
'''
def process_type1(lines, results):
    header_nm_re = re.compile(r'@nm\s+t="([^"]+)"\s+s=([^\s]+)')
    header_saudio_re = re.compile(
        r'@saudio\s+'
        r't="(?P<speaker>[^"]+)"\s+'
        r'fv=(?P<voice1>[^\s]+)\s+'
        r'front="(?P<text1>[^"]+)"\s+'
        r'bv=(?P<voice2>[^\s]+)\s+'
        r'back="(?P<text2>[^"]+)"'
    )

    i = 0
    while i < len(lines):
        line = lines[i]
        m_nm = header_nm_re.match(line)
        m_s = header_saudio_re.match(line)

        if m_nm:
            speaker = m_nm.group(1)
            voice   = m_nm.group(2)

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
            continue

        elif m_s:
            speaker = m_s.group('speaker')

            # first (front) entry
            voice1 = m_s.group('voice1')
            text1  = text_cleaning_02(m_s.group('text1'))
            results.append({
                "Speaker": speaker,
                "Voice": voice1,
                "Text":   text1
            })

            # second (back) entry
            voice2 = m_s.group('voice2')
            text2  = text_cleaning_02(m_s.group('text2'))
            results.append({
                "Speaker": speaker,
                "Voice": voice2,
                "Text":   text2
            })

            i += 1
            continue

        i += 1

'''
@msg name="晴菜" voice="vo_har_1044"
「ご主人様、お願いがあります！」
@msgend
'''
def process_type1_1(lines, results):
    # 形如：@msg name="Speaker" voice="Voice"
    header_re = re.compile(r'^@msg\b(.*)$')
    # 抽取形如 key="value" 的属性对；允许有任意空格
    attr_re   = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()
        m = header_re.match(line)
        if not m:
            i += 1
            continue

        # 解析属性
        attr_str = m.group(1)
        attrs = dict(attr_re.findall(attr_str))

        Speaker = (attrs.get('name') or '').replace('　', '')
        Voice   = attrs.get('voice') or None

        # 收集正文直到 @msgend
        i += 1
        tmp = []
        while i < n and not lines[i].strip().startswith('@msgend'):
            tmp.append(lines[i])
            i += 1

        Text = text_cleaning_02(''.join(tmp))
        results.append({
            "Speaker": Speaker,
            "Voice":   Voice,
            "Text":    Text
        })

        # 跳过 @msgend 行（如果存在）
        if i < n and lines[i].strip().startswith('@msgend'):
            i += 1

    return results

'''
@vo est0010
【エスト/女の子】
「わたし、エスト・フラグレンスと申します」
'''
def process_type1_2(lines, results):
    # @vo Voice
    vo_re = re.compile(r'^\s*@vo\s+(.+?)\s*$')
    # 【Speaker】
    spk_re = re.compile(r'^\s*【([^】]+)】\s*$')

    current_voice = None
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 1) 处理 @vo
        m_vo = vo_re.match(line)
        if m_vo:
            current_voice = m_vo.group(1).strip() or None
            i += 1
            continue

        # 2) 处理 【Speaker】
        m_spk = spk_re.match(line)
        if m_spk:
            speaker = m_spk.group(1).replace('　', '').strip()
            speaker = speaker.split('/')[0]
            i += 1

            # 3) 收集文本直到遇到下一个块起点
            tmp = []
            while i < n:
                if spk_re.match(lines[i]) or vo_re.match(lines[i]):
                    break
                tmp.append(lines[i])
                i += 1

            text = text_cleaning_02(''.join(tmp))
            results.append({
                "Speaker": speaker,
                "Voice":   current_voice,
                "Text":    text
            })
            continue

        # 非 @vo / 非 Speaker 行：跳过
        i += 1
