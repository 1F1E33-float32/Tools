import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"E:\Dataset\FuckGalGame\minori\Tsumi no Hikari Rendezvous Mikan Blossom\script")
    parser.add_argument("-op", type=str, default=r'D:\AI\Audio_Tools\python\1.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r"\\[a-zA-Z]", '', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    return text

def message(line):
    match1 = re.match(r"\.message\s([^ ]+)\s([^ ]+)\s([^ ]+)\s([^ ]+)", line, re.DOTALL)
    if match1:
        voice = match1.group(2)
        voice = re.sub(r"\[.*?\]", '', voice)
        speaker = match1.group(3)
        text = match1.group(4).strip()
        return speaker, voice, text
    else:
        match2 = re.match(r"\.message (.+) (.+)\s{2,}(.+)", line, re.DOTALL)
        if match2:
            voice = match2.group(2).strip()
            voice = re.sub(r"\[.*?\]", '', voice)
            speaker = '旁白'
            text = match2.group(3).strip()
            return speaker, voice, text
        else:
            return None

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.sc", recursive=True)
    results = []
    for filename in tqdm(filelist):
        with open(filename, 'r', encoding='cp932') as file:
            lines = file.readlines()
        lines = [re.sub(r'\{.*?\}', '', line.strip()).replace('\\n', '').replace('#', '').replace('　', '').replace('@', '') for line in lines]
        for i, line in enumerate(lines):
            details = message(line)
            if details:
                speaker, voice, text = details
                text = text_cleaning(text)
                if not text:
                    continue
                results.append((speaker, voice, text))

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
    main(args.JA, args.op)