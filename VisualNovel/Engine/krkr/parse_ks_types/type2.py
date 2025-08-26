import re
from .text_cleaning import text_cleaning_02

'''
[天使 vo=vo1_0001 text="？？？"]
[>>]いや惚れろよ、このビューチーな私に[<<][c]
'''
def process_type2(lines, results):
    speaker_re = re.compile(r'\[(?P<Speaker>[^\s]+)\s+vo=(?P<Voice>\S+)[^\]]*\]')
    text_re    = re.compile(r'\[>>\](?P<Text>.*?)\[<<\]\[c\]')
    current = {}
    for i, line in enumerate(lines):
        m1 = speaker_re.search(line)
        if m1:
            current['Speaker'] = m1.group('Speaker')
            current['Voice']   = m1.group('Voice')
            continue

        m2 = text_re.search(line)
        if m2 and 'Speaker' in current:
            results.append({
                "Speaker": current['Speaker'],
                "Voice":   current['Voice'],
                "Text":    text_cleaning_02(m2.group('Text').strip())
            })
            current.clear()
    return results
