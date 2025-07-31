import re
import json
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.TXT", recursive=True)
    
    results = []

    for filename in tqdm(filelist):
        with open(filename, 'r', encoding='cp932') as file:
            lines = file.readlines()

        i = 0   
        while i < len(lines):
            if lines[i].startswith(';'):
                i += 1
                continue

            voice_match = re.compile(r'\$VOICE,v\\(\w+\.ogg)').search(lines[i])
            if voice_match:
                Voice = voice_match.group(1).replace('.ogv', '').replace('.ogg', '')
                Speaker_id = Voice.split('_')[0]
                i += 1

                while i < len(lines):
                    if lines[i].startswith(';'):
                        i += 1
                        continue

                    speaker_match = re.compile(r'【([^】]+)】').search(lines[i])
                    if speaker_match:
                        Speaker = speaker_match.group(1)
                        Speaker = Speaker.split('/')[0]
                        i += 1

                        text_lines = []
                        while i < len(lines):
                            if lines[i].strip() == '':
                                i += 1
                                break
                            if lines[i].startswith(';'):
                                i += 1
                                continue
                            text_lines.append(lines[i].strip())
                            i += 1

                        Text = ''.join(text_lines)
                        Text = text_cleaning(Text)
                        results.append((Speaker, Speaker_id, Voice, Text))
                        break  # 跳出 speaker 匹配的循环
                    else:
                        i += 1
            else:
                i += 1

    replace_dict = {}
    for Speaker, Speaker_id, Voice, Text in tqdm(results):
        if Speaker != '？？？' and Speaker_id not in replace_dict:
            replace_dict[Speaker_id] = Speaker

    fixed_results = []
    for Speaker, Speaker_id, Voice, Text in tqdm(results):
        if Speaker == '？？？' and Speaker_id in replace_dict:
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