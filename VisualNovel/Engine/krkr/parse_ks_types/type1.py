import re
from .text_cleaning import text_cleaning_02

'''
@nm t="臨" s=rin_0015
「んー、特には何も。[r]
　そっちが寂しいかなーって思ってさ」[np]

@nm t="西学園生"（♂） s=aaj_0003
「こんにちは」[np]

@nm rt="克人" t="？？？" s=kat_0003
「私は才華の父、橘克人だ。よろしく」[np]

@saudio t="詩乃" fv=shi_0056 front="「わ、わかりました」" bv=shu_0024 back="「あとで観るのっ！？　そんなの、は、恥ずかしい……」"
'''
def process_type1(lines, results):
    patterns = {
        'nm_general': re.compile(r'@nm\s+(.+)'),  # 匹配@nm后的所有参数
        'saudio': re.compile(
            r'@saudio\s+'
            r't="(?P<speaker>[^"]+)"\s+'
            r'fv=(?P<voice1>[^\s]+)\s+'
            r'front="(?P<text1>[^"]+)"\s+'
            r'bv=(?P<voice2>[^\s]+)\s+'
            r'back="(?P<text2>[^"]+)"'
        )
    }

    def handle_nm_line(line, line_index):
        """处理@nm格式，支持任意顺序的参数"""
        # 提取所有参数
        rt_match = re.search(r'rt="([^"]+)"', line)
        t_match = re.search(r't="([^"]+)"', line)
        s_match = re.search(r's=([^\s]+)', line)
        
        if not s_match:
            return line_index + 1  # 没有voice信息，跳过
            
        voice = s_match.group(1)
        
        # 优先使用rt=的值，否则使用t=的值
        if rt_match:
            speaker = rt_match.group(1)
        elif t_match:
            speaker = t_match.group(1)
        else:
            return line_index + 1  # 既没有rt也没有t，跳过
            
        return _collect_multiline_text(line_index, speaker, voice)

    def handle_saudio(match, line_index):
        """处理@saudio格式"""
        speaker = match.group('speaker')
        
        # 添加第一个条目 (front)
        voice1 = match.group('voice1')
        text1 = text_cleaning_02(match.group('text1'))
        results.append({
            "Speaker": speaker,
            "Voice": voice1,
            "Text": text1
        })
        
        # 添加第二个条目 (back)
        voice2 = match.group('voice2')
        text2 = text_cleaning_02(match.group('text2'))
        results.append({
            "Speaker": speaker,
            "Voice": voice2,
            "Text": text2
        })
        
        return line_index + 1

    def _collect_multiline_text(start_index, speaker, voice):
        tmp = []
        i = start_index + 1
        while i < len(lines):
            text_line = lines[i]
            
            # 如果遇到@overlap_ch，放弃本次收集
            if text_line.strip().startswith('@overlap_ch'):
                # 继续移动到文本结束位置，但不保存结果
                while i < len(lines):
                    if '[np' in lines[i] or '[wvl' in lines[i]:
                        break
                    i += 1
                return i + 1
            
            # 跳过@chr、@chr2、@chr_poschange等命令行
            if text_line.strip().startswith('@'):
                i += 1
                continue
            
            # 处理行内的[chr2 ...]标签，去除这些标签但保留文本
            # 例如：[chr2 st05jc080b rt="依那"]　わーごめんなさい！！
            text_line = re.sub(r'\[chr2?\s+[^\]]+\]', '', text_line)
            
            tmp.append(text_line)
            if '[np' in text_line or '[wvl' in text_line:
                break
            i += 1
        
        text = ''.join(tmp)
        text = text_cleaning_02(text)
        
        results.append({
            "Speaker": speaker,
            "Voice": voice,
            "Text": text
        })
        
        return i + 1

    # 主处理循环
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 使用类似switch-case的结构
        matched = False
        
        # Case 1: @nm (支持任意顺序的rt=, t=, s=参数)
        match = patterns['nm_general'].match(line)
        if match:
            i = handle_nm_line(line, i)
            matched = True
        
        # Case 2: @saudio ...
        if not matched:
            match = patterns['saudio'].match(line)
            if match:
                i = handle_saudio(match, i)
                matched = True
        
        # 如果没有匹配任何模式，继续下一行
        if not matched:
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
