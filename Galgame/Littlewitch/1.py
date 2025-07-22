import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\Script.dat~")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\([^)]*\)', '', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.txt", recursive=True)
    results = []

    for filename in tqdm(filelist):
        with open(filename, 'r', encoding='cp932') as file:
            lines = file.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]
            # detect a message block
            if line.startswith('-message'):
                # extract speaker id and voice attributes
                sp_match = re.search(r'id="([^"]+)"', line)
                vo_match = re.search(r'voice="([^"]+)"', line)
                if sp_match and vo_match:
                    speaker = sp_match.group(1)
                    voice   = vo_match.group(1).replace('.ogg', '')

                    # gather text lines until a line that's just a backslash
                    text_buf = []
                    i += 1
                    while i < len(lines) and lines[i].strip() != '\\':
                        text_buf.append(lines[i].rstrip('\n'))
                        i += 1

                    # join and clean up
                    raw_text = ''.join(text_buf)
                    clean_text = text_cleaning(raw_text)

                    results.append((speaker, voice, clean_text))
            i += 1

    # dedupe and write out JSON
    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            if Voice not in seen:
                seen.add(Voice)
                json_data.append({
                    'Speaker': Speaker,
                    'Voice':   Voice,
                    'Text':    Text
                })
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)