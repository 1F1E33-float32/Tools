import re

from .text_cleaning import text_cleaning_01


def process_type999(lines, results):
    name_mapping = {
        "ZYCs": "周御城",
        "FHs": "风华",
        "XXYs": "夏雪源",
        "HXYs": "郝心语",
        "HSJs": "郝思嘉",
        "AASs": "安妮",
        "LXAs": "吕小艾",
        "ZSs": "子受",
        "QQs": "清秋",
        "BYWYs": "北野微云",
        "LHNs": "律华娜",
        "LHYs": "林海岩",
        "JFs": "伊阿宋",
        "AcMs": "店 员",
        "SPs": "店员",
        "XTSs": "夏天水",
        "HQSs": "郝千殇",
        "NYBCs": "南苑白草",
        "AGRs": "阿纳托利",
        "BSs": "宾森",
        "JZGs": "迦至刚",
        "OYLLs": "欧阳涟里",
        "LWJs": "陆惟君",
        "ATs": "爱丽丝",
        "ZZYs": "邹之颖",
        "HAMs": "海曼霍根",
        "SLs": "汐斯",
        "JWAs": "江外安",
        "LvHYs": "吕华音",
        "WQWs": "武其文",
        "RBSs": "任泊时",
        "STXPs": "司徒修平",
        "JSTs": "蒋仕腾",
        "WZFs": "亡踪坊",
        "CYQs": "淳于权",
        "MMs": "米兰塔",
        "XLs": "徐岚",
        "XXLs": "徐香兰",
        "HSs": "韩随",
        "AdTs": "阿德蕾迪丝",
        "LuWJs": "陆为军",
        "BSYs": "宾森",
        "HQSYs": "郝千殇",
        "AMs": "阿缇密斯",
        "EMs": "埃万盖洛斯",
        "UIs": "幽波丽池",
        "PRs": "教授",
        "MIBAs": "西装男",
        "MIBBs": "西装男",
        "MIBCs": "西装男",
        "LCs": "猎人",
        "RFAs": "研究员",
        "RFBs": "助理研究员",
        "RFCs": "副研究员",
        "PMAs": "警司",
        "PMBs": "警员",
        "SGs": "保安",
        "EnNOs": "enja士官",
        "EnPAs": "enja士兵",
        "EnPBs": "enja士兵",
        "EnPCs": "enja士兵",
        "RNOs": "叛乱士官",
        "RPAs": "叛乱士兵",
        "RPBs": "叛乱士兵",
        "RPCs": "叛乱士兵",
        "SaNOs": "天工会士官",
        "SaPAs": "天工会士兵",
        "SaPBs": "天工会士兵",
        "SaPCs": "天工会士兵",
        "ErNOs": "启示学会士官",
        "ErPAs": "启示学会士兵",
        "ErPBs": "启示学会士兵",
        "ErPCs": "启示学会士兵",
        "StNOs": "STW士官",
        "StPAs": "STW士兵",
        "StPBs": "STW士兵",
        "StPCs": "STW士兵",
        "EkCos": "教会指挥官",
        "EkChAs": "教会骑士",
        "EkChBs": "教会骑士",
        "EkChCs": "教会骑士",
        "DRs": "医生",
        "NSs": "护士",
        "SCs": "秘书",
        "EnSuAs": "部下",
        "EnSuBs": "部下",
        "RSuAs": "部下",
        "RSuBs": "部下",
        "SaSuAs": "部下",
        "SaSuBs": "部下",
        "ErSuAs": "部下",
        "ErSuBs": "部下",
        "StSuAs": "部下",
        "StSuBs": "部下",
        "MCs": "群众",
        "PSs": "群众",
        "STs": "群众",
        "WKs": "群众",
        "UMs": "男性的声音",
        "CoAs": "真言师",
        "CoBs": "真言师",
        "CoCs": "真言师",
        "ColAs": "同僚",
        "ColBs": "同僚",
        "MaWos": "妇人",
        "RaOps": "雷达操作员",
    }
    speaker_re = re.compile(r"\[(?P<Code>[^\s\]]+)\s+[^\]]*\]")
    playvc_re = re.compile(r'\[playvc\s+storage="?([^"\]]+)"?\]')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m_s = speaker_re.match(line)
        if not m_s:
            i += 1
            continue

        code = m_s.group("Code")
        speaker = name_mapping.get(code)
        if not speaker:
            i += 1
            continue

        i += 1
        voice = None
        while i < len(lines):
            m_v = playvc_re.match(lines[i].strip())
            if m_v:
                voice = m_v.group(1)
                i += 1
                break
            i += 1

        if voice is None:
            continue

        text_chunks = []
        while i < len(lines):
            txt_line = lines[i]
            if "[p]" in txt_line:
                final = txt_line.replace("[p]", "").strip()
                if final:
                    text_chunks.append(final)
                i += 1
                break
            clean = txt_line.strip()
            if clean:
                text_chunks.append(clean)
            i += 1

        full_text = "".join(text_chunks)
        results.append({"Speaker": speaker, "Voice": voice, "Text": text_cleaning_01(full_text)})
        speaker = voice = None
