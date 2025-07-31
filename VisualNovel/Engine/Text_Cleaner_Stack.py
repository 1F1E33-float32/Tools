import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\sc")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = text.replace('\\n', '').replace('\n', '').replace('　', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.ORS", recursive=True)
    results = []
    for filename in tqdm(filelist):
        with open(filename, 'r', encoding='cp932', errors='replace') as file:
            lines = file.readlines()
        
        lines = [line.strip() for line in lines if line.strip() != '']

        for i, line in enumerate(lines):
            if i <= len(lines) - 2 and line.startswith('[PrintText]') and lines[i + 1].startswith('[PlayVoice]'):
                match = re.match(r'\[PrintText\]="[^"]*?(\d{2}:\d{2}:\d{2}),\s*([^,]+?),\s*([^,]+?),\s*(\d{2}:\d{2}:\d{2})";', line)
                Speaker = match.group(2)
                Text = text_cleaning(match.group(3))
                match = re.match(r'\[PlayVoice\]="[^"]*?(\d{2}:\d{2}:\d{2}),\s*([^,]+?),\s*([^,]+?),\s*([^,]+?),\s*(\d{2}:\d{2}:\d{2})";', lines[i + 1])
                Voice = match.group(2)
                Voice = Voice.split('/')[-1]
                results.append((Speaker, Voice, Text))

    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            if Voice.lower() not in seen:
                seen.add(Voice.lower())
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)