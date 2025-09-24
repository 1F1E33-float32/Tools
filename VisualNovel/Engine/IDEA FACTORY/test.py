import re

_HONORIFICS = "ちゃん|君|くん|さん|様|先輩|先生"

_RE_NAME_TOKEN = re.compile(r"#Name\[(\d+)\]")
_RE_NAME_IN_QUOTES = [
    re.compile(r"[「『]\s*#Name\[\d+\]\s*[」』]"),
    re.compile(r"[（(]\s*#Name\[\d+\]\s*[）)]"),
    re.compile(r"['\"]\s*#Name\[\d+\]\s*['\"]"),
]
_RE_NAME_WITH_HONORIFIC = re.compile(rf"#Name\[\d+\](?:{_HONORIFICS})")


def _clean_placeholder_names(text: str) -> str:
    s = text

    # 1) Remove quoted name tokens entirely (including the quotes)
    for rx in _RE_NAME_IN_QUOTES:
        s = rx.sub("", s)

    # 2) Remove name tokens with immediate honorific suffix
    s = _RE_NAME_WITH_HONORIFIC.sub("", s)

    # 3) Remove bare name tokens
    s = _RE_NAME_TOKEN.sub("", s)

    # 4) Punctuation cleanup
    # Collapse duplicated punctuation
    s = re.sub(r"[、]{2,}", "、", s)
    s = re.sub(r"[。]{2,}", "。", s)
    s = re.sub(r"、。", "。", s)
    s = re.sub(r"[！？]{3,}", lambda m: m.group(0)[0] * 2, s)  # cap at double
    s = re.sub(r"！！+", "！", s)
    s = re.sub(r"？？+", "？", s)

    # Remove empty quote pairs created by deletions
    s = s.replace("「」", "").replace("『』", "").replace("()", "").replace("（）", "")

    # Trim punctuation at start/end
    s = re.sub(r"^[、。！？\s]+", "", s)
    s = re.sub(r"[\s]+$", "", s)

    # Fix cases like '、』' or '、」' -> '』' / '」'
    s = s.replace("、』", "』").replace("、」", "」")

    return s

if __name__ == "__main__":
    text = "#Name[1]君、イッキュウはこの際無視していい。さ、食べてくれ"
    c = _clean_placeholder_names(text)
    print(text)
    print(c)