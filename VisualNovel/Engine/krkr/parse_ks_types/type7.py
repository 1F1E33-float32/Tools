import re

from .text_cleaning import text_cleaning_02


def process_type7_0(lines, results):
    """
    [菜穂子 voice=D10750]
    【菜穂子】
    「公序良俗に反した行いがなければ、止め立てする理由は
    私たちにはないということ」
    """
    header_re = re.compile(r"^\[([^\s\]]+)\s+voice=([^\]\s]+)")

    while lines:
        line = lines[0].strip()
        m = header_re.match(line)
        if not m:
            lines.pop(0)
            continue

        speaker = m.group(1)
        voice = m.group(2)
        lines.pop(0)

        if lines and lines[0].strip().startswith("【") and lines[0].strip().endswith("】"):
            lines.pop(0)

        text_lines = []
        while lines:
            ln = lines[0]
            if ln == "":
                lines.pop(0)
                break
            text_lines.append(ln)
            lines.pop(0)
        text_lines = "".join(text_lines)
        text_lines = text_cleaning_02(text_lines)

        results.append({"Speaker": speaker, "Voice": voice, "Text": text_lines})
