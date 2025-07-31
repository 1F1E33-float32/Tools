import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('▼', '').replace('　', '').replace('●', '')
    text = re.sub(r"#\d+", '', text)
    text = text.replace('#', '')
    return text

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.scd", recursive=True)
    results = []
    for filename in tqdm(filelist):
        with open(filename, 'r', encoding='cp932') as file:
            lines = file.readlines()
        
        lines = [line.strip() for line in lines]

        for i, line in enumerate(lines):
            match = re.findall(r'\*NAME\s+"(.*?)"\s*,\s*(.*)', line)
            if match:
                match = match[0]
                Speaker = match[0]
                Voice = match[1]
                Voice = Voice.replace('(', '').replace(')', '')
                if lines[i + 1].startswith('*TEXT'):
                    Text = lines[i + 2]
                    Text = text_cleaning(Text)
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