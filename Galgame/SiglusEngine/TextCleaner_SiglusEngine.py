import re
import json
import argparse
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\ss")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def speaker_cleaning(speaker_ori):
    speaker = speaker_ori.split('／')[0]
    speaker = speaker.replace('◎', '').replace('★', '')
    return speaker

def text_cleaning(text):
    text = re.sub(r'ruby\(([^)]+)\)\s*(.+?)\s*ruby', r'\1', text)
    text = re.sub(r'\{[^:]*:([^}]*)\}', r'\1', text)
    text = re.sub(r'（[^）]*$|@([a-zA-Z_]+)\((.*?)\)|『.*?』|', '', text)
    text = re.sub(r'[A-Za-z_]+\(\d+\)\s*', '', text)
    text = text.replace('" "', '').replace('nli', '').replace('NLI', '')
    text = text.replace('"', '').replace('『', '').replace('』', '').replace('〝', '').replace('〟', '').replace('ヽ ', '')
    text = text.replace('　', '').replace('／／／', '').replace('@heart', '').replace('〈', '').replace('〉', '').replace('@', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.ss", recursive=True)
    results = []
    seen_voices = set()

    for files in filelist:
        try:
            with open(files, 'r', encoding='cp932') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            with open(files, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        
        lines = [re.sub(r'timewait\(\d+\)', '', line.strip()) for line in lines]
        print(files)

        for i, line in enumerate(lines):
            if line.startswith('//'):
                continue
            if 'multi_msg' in line or '@KOE' in line:
                continue
            if (match := re.search(r"KOE\((\d+),\d+\).*?【(.+?)】", line)):
                Voice = match.group(1)
                Voice = f"z{Voice[:4]}#{Voice[4:]}"
                Speaker = speaker_cleaning(match.group(2))

                # 只在剩下的字符串中搜索文本内容
                rest_line = line[match.end():]
                if (text_match := re.search(r"[「『（](.+?)[」』）]", rest_line)):
                    Text = text_match.group(1)
                try:
                    Text = text_cleaning(Text)
                except:
                    continue
                if "(" in Text: # 摆烂了，屎太多了，懒得清理了
                    continue
                if Voice in seen_voices:
                    print(f"重复的 Voice: {Voice}, Speaker: {Speaker}, Text: {Text}")
                else:
                    seen_voices.add(Voice)
                    results.append((Speaker, Voice, Text))
            
    with open(op_json, mode='w', encoding='utf-8') as file:
        json_data = [{'Speaker': Speaker, 'Voice': Voice, 'Text': Text} for Speaker, Voice, Text in results]
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)