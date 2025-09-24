import re


def text_cleaning_01(text):
    text = text.replace("\n", "")
    text = re.sub(r"\[([^\]]+?)'[^]]+\]", r"\1", text)
    text = re.sub(r"\['([^']+?) text=\"[^\"]+?\"\]", r"\1", text)
    text = re.sub(r"＃\([^()]+\) ", "", text)
    text = text.replace("[r]", "").replace("[np]", "")
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "").replace('"', "").replace('"', "")
    text = text.replace("　", "")
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = text.replace('"', "")
    return text


def text_cleaning_02(text):
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("／", "").replace("\n", "")
    return text
