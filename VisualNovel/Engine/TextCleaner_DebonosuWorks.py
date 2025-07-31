import re
import json
import argparse
import subprocess
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def clean_file(file):
    new_lines = []
    skip_next_line = False  # 用于标记是否需要跳过下一行

    for line in file:
        if skip_next_line:
            skip_next_line = False  # 跳过当前行
            continue  # 跳过下一行

        match = re.search(r'; (.*)', line)
        if match:
            content = match.group(1).strip()
            content = content.replace('"', '')  # 去除双引号
            if content in ['page', 'stand']:
                skip_next_line = True  # 标记跳过下一行
            else:
                new_lines.append(content)

    return new_lines

def text_cleaning(text):
    text = re.sub(r'\{([^/]+)\/[^}]+\}', r'\1', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '')
    text = text.replace('♪', '').replace('・', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.scb", recursive=True)
    results = []
    for filename in tqdm(filelist):
        result = subprocess.run(['luac.exe', filename], capture_output=True, text=True, encoding='cp932')
        file = result.stdout.splitlines()
        new_lines = clean_file(file)

        is_find_speaker = False
        is_find_text = False

        for i, line in enumerate(new_lines):
            if line == 'playvoice':
                Voice = new_lines[i + 1]
                Speaker_id = re.match(r'^([A-Za-z]+)\d+', Voice)
                if Speaker_id:
                    Speaker_id = Speaker_id.group(1)
                    is_find_speaker = True

            if line == 'name' and is_find_speaker:
                Speaker = new_lines[i + 1]
                Speaker = Speaker.replace(' ', '')
                is_find_speaker = False
                is_find_text = True

            if line == '_text' and is_find_text:
                Text = new_lines[i + 1]
                Text = text_cleaning(Text)
                is_find_text = False
                results.append((Speaker, Speaker_id, Voice, Text))
    
    replace_dict = {}
    for Speaker, Speaker_id, Voice, Text in tqdm(results):
        if Speaker != '？？？' and Speaker != '' and Speaker_id not in replace_dict:
            replace_dict[Speaker_id] = Speaker

    fixed_results = []
    for Speaker, Speaker_id, Voice, Text in tqdm(results):
        if (Speaker == '？？？' or Speaker == '') and Speaker_id in replace_dict:
            fixed_results.append((replace_dict[Speaker_id], Speaker_id, Voice, Text))
        else:
            fixed_results.append((Speaker, Speaker_id, Voice, Text))

    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Speaker_id, Voice, Text in fixed_results:
            if Voice not in seen:
                seen.add(Voice)
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)