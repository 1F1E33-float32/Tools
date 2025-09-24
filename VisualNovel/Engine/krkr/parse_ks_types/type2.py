import re

from .text_cleaning import text_cleaning_02


def process_type2_0(lines, results):
    """
    [天使 vo=vo1_0001 text="？？？"]
    [>>]いや惚れろよ、このビューチーな私に[<<][c]
    """
    speaker_re = re.compile(r"\[(?P<Speaker>[^\s]+)\s+vo=(?P<Voice>\S+)[^\]]*\]")
    text_re = re.compile(r"\[>>\](?P<Text>.*?)\[<<\]\[c\]")
    current = {}
    for i, line in enumerate(lines):
        m1 = speaker_re.search(line)
        if m1:
            current["Speaker"] = m1.group("Speaker")
            current["Voice"] = m1.group("Voice")
            continue

        m2 = text_re.search(line)
        if m2 and "Speaker" in current:
            results.append({"Speaker": current["Speaker"], "Voice": current["Voice"], "Text": text_cleaning_02(m2.group("Text").strip())})
            current.clear()


def process_type2_1(lines, results):
    """
    [マルエット v=vs182 f=07]「ちょっと！　隊長！」[k]
    [name n=化け物]「グオッ！！」[k]
    """
    chunk_re = re.compile(
        r"\["
        r"(?P<first>[^\s\]]+)"  # 第一个标记
        r"(?P<params>(?=[^\]]*\bv=)[^\]]*)"  # 必须包含 v= 的参数区
        r"\]"
        r"(?P<Text>.*?)"  # 到最近 [k] 为止（非贪婪）
        r"\[k\]",
        flags=re.DOTALL,
    )

    # 参数提取
    n_re = re.compile(r"\bn=([^\s\]]+)")
    v_re = re.compile(r"\bv=([^\s\]]+)")

    # 文本中的换行标记
    r_token_re = re.compile(r"\[r\]")

    for line in lines:
        for m in chunk_re.finditer(line):
            first = m.group("first")
            params = m.group("params") or ""
            raw_text = m.group("Text")

            # Voice（必须）
            v_m = v_re.search(params)
            if not v_m:
                continue
            voice = v_m.group(1)

            # Speaker：n= 优先，否则用第一个标记
            n_m = n_re.search(params)
            speaker = n_m.group(1) if n_m else first

            # 处理 [r] → 换行，然后清洗
            text = r_token_re.sub("\n", raw_text)
            text = text_cleaning_02(text.strip())

            if speaker and voice and text:
                results.append({"Speaker": speaker, "Voice": voice, "Text": text})
