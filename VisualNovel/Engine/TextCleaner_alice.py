import re
import json
import argparse

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"E:\Dataset\FuckGalGame\Alice Soft\Rance 03 - Leazas Kanraku\script.txt")
    parser.add_argument("-op", type=str, default=r'D:\AI\Audio_Tools\python\1.json')
    parser.add_argument("-ft", type=str, default=0)
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\[.*?\]|\([^()]*\)', '', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace('／', '')
    return text

def main(JA_file, op_json, force_type):
    with open(JA_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines if not line.strip().startswith("PUSH") and not line.strip().startswith("CALLFUNC ■")]

    results = []
    for i, line in enumerate(lines):
        if line == "CALLFUNC VOICE":
            if force_type == 0:
                Speaker = re.findall(r'S_PUSH\s*"([^"]+)"', lines[i - 4])
                if not Speaker:
                    continue
                Speaker = Speaker[0].split('／')[0]
            if force_type == 1:
                Speaker = re.findall(r'S_PUSH\s*"([^"]+)"', lines[i - 4])
                if not Speaker:
                    continue
                Speaker = Speaker[0].split('／')[1]
            Voice = re.findall(r'S_PUSH\s*"([^"]+)"', lines[i - 1])[0]

            Text = ""
            for j in range(i + 1, len(lines)):
                if lines[j] == 'RETURN':
                    break
                elif lines[j] == 'CALLFUNC A':
                    results.append((Speaker, Voice, Text))
                    break
                elif lines[j] == 'CALLFUNC R':
                    continue
                elif lines[j].startswith('MSG'):
                    sub_text = re.findall(r'"([^"]*)"', lines[j])[0]
                    Text += text_cleaning(sub_text)

    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            record = (Speaker, Voice, Text)
            if record not in seen:
                seen.add(record)
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op, args.ft)