import re
from .text_cleaning import text_cleaning_02

'''
@Voice
【Speaker】
Text

@Voice sketch
@【Speakerスケブ】 制服２ 正面 スケブ 通常 奥 中
@スケブ text="Text"

@Speaker voice=Voice
【Speaker】
Text
'''
def process_type4(lines, results):
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # —— 形式 3: @Speaker voice=Voice
        mC = re.match(r'^@(?P<Speaker>[^\s]+)\s+voice=(?P<Voice>[^\s]+)$', line)
        if mC:
            speaker = mC.group('Speaker')
            voice   = mC.group('Voice')
            # 下行应该是 【Speaker】
            if i + 1 < len(lines):
                mS = re.match(r'^【(?P<SPEAK>[^\]]+)】$', lines[i+1].strip())
                if mS:
                    # 再下一行就是 Text
                    text = lines[i + 2]
                    results.append({
                        "Speaker": speaker.split('/')[0],
                        "Voice":   voice,
                        "Text":    text_cleaning_02(text.replace('/', ''))
                    })
                    i += 3
                    continue

        # —— 形式 2: @Voice sketch
        mB = re.match(r'^@(?P<Voice>[^\s]+)\s+\w+$', line)
        if mB and 'sketch' in line:
            voice = mB.group('Voice')
            # 下行形如 @【Speakerスケブ】
            if i + 1 < len(lines):
                mSB = re.match(r'^@【(?P<Speaker>[^】]+)】', lines[i+1])
                if mSB:
                    speaker = mSB.group('Speaker')
                    # 再下一行形如 @スケブ text="Text"
                    if i + 2 < len(lines):
                        mT = re.match(r'^@\S+\s+text="(?P<Text>.*)"', lines[i+2])
                        if mT:
                            text = mT.group('Text')
                            results.append({
                                "Speaker": speaker.split('/')[0],
                                "Voice":   voice,
                                "Text":    text_cleaning_02(text.replace('/', ''))
                            })
                            i += 3
                            continue

        # —— 形式 1: @Voice
        mA = re.match(r'^@(?P<Voice>[^\s]+)$', line)
        if mA:
            voice = mA.group('Voice')
            # 下行应该是 【Speaker】
            if i + 1 < len(lines):
                mS = re.match(r'^【(?P<Speaker>[^】]+)】$', lines[i+1].strip())
                if mS:
                    speaker = mS.group('Speaker')
                    # 再下一行就是 Text
                    text = lines[i + 2]
                    results.append({
                        "Speaker": speaker.split('/')[0],
                        "Voice":   voice,
                        "Text":    text_cleaning_02(text.replace('/', ''))
                    })
                    i += 3
                    continue
        i += 1

    return results
