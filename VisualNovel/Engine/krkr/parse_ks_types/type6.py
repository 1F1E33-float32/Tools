import re

from .text_cleaning import text_cleaning_02


def process_type6_0(lines, results):
    """
    @満花 voice=C01_いもうと２_エンド01_0027.ogg
    【満花】　「あっあっあっ、あああん、気持ちいい……」
    """
    current_speaker = None
    current_voice = ""

    header_re = re.compile(r"^@(?P<Speaker>\S+)\s+voice=(?P<Voice>\S+)")
    text_re = re.compile(r"^【.*?】　「?(?P<Text>.+?)」?$")

    for line in lines:
        m1 = header_re.match(line)
        if m1:
            current_speaker = m1.group("Speaker")
            current_voice = m1.group("Voice").split(".")[0]
            continue

        if current_speaker is not None:
            m2 = text_re.match(line)
            if m2:
                raw_text = m2.group("Text").strip()
                cleaned = text_cleaning_02(raw_text)
                results.append({"Speaker": current_speaker, "Voice": current_voice, "Text": cleaned})


def process_type6_1(lines, results):
    current_speaker = None
    current_voice = ""
    expecting_text = False

    # Header regex now matches voice in double quotes
    header_re = re.compile(r'^@(?P<Speaker>\S+)\s+voice="(?P<Voice>[^"]*)"')

    for line in lines:
        m1 = header_re.match(line)
        if m1:
            current_speaker = m1.group("Speaker")
            current_speaker = current_speaker.split("/")[0]
            current_voice = m1.group("Voice").split(".")[0]
            expecting_text = True
            continue

        if expecting_text and current_speaker is not None:
            raw_text = line.strip()
            cleaned = text_cleaning_02(raw_text)
            results.append({"Speaker": current_speaker, "Voice": current_voice, "Text": cleaned})
            expecting_text = False
