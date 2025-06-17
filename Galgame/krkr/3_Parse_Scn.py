import os
import re
import json
import argparse
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-ft", type=int, default=0)
    return parser.parse_args(args=args, namespace=namespace)

def read_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def text_cleaning(text):
    text = text.replace('\n', '').replace(r'\n', '')
    text = re.sub(r"%[^;]*;|#[^;]*;|%\d+|\[[^[\\\/]*\]", '', text)
    text = text.replace('\\x', '')
    text = text.replace('\\', '')
    text = text.replace('\n', '')
    text = text.replace('%D$vl1', '')
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '').replace('“', '').replace('”', '').replace('≪', '').replace('≫', '')
    text = text.replace(r'　', '').replace('♪', '').replace('♥', '').replace('%r', '').replace('\u3000', '')
    return text

def process_type0(_0_JA_data):
    results = []
    if 'scenes' in _0_JA_data:
        for _1_JA_scenes in _0_JA_data['scenes']:
            if 'texts' in _1_JA_scenes:
                for _2_JA_texts in _1_JA_scenes['texts']:
                    Speaker = Voice = Text = None
                    if _2_JA_texts[2] is not None:
                        Speaker = _2_JA_texts[2][0]['name']
                        Voice = _2_JA_texts[2][0]['voice'].lower()
                        
                    text_entry = _2_JA_texts[1][0]
                    if len(text_entry) > 3 and text_entry[3]:
                        Text = text_cleaning(text_entry[3])
                    else:
                        Text = text_cleaning(text_entry[1])

                    results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
    return results

def process_type1(jdata):
    return []

def process_type2(jdata):
    return []

PROCESSORS = {0: process_type0, 1: process_type1, 2: process_type2}
def main(ja_dir, op_json, force_type):
    if force_type not in PROCESSORS:
        raise ValueError(f"Unsupported type: {force_type}")

    files = []
    for r, _, fs in os.walk(ja_dir):
        for f in fs:
            if f.endswith('.json') and not f.endswith('.resx.json'):
                files.append(os.path.join(r, f))

    results = []
    scene_idx = 0

    for path in tqdm(files, desc="processing"):
        jdata = read_json_file(path)
        items = PROCESSORS[force_type](jdata)

        for line_idx, item in enumerate(items):
            item['scene'] = scene_idx
            item['line'] = line_idx
            results.append(item)

        scene_idx += 1

    with open(op_json, 'w', encoding='utf-8') as fp:
        json.dump(results, fp, ensure_ascii=False, indent=4)

    out_list = r"D:\Fuck_galgame\files.txt"
    with open(out_list, 'w', encoding='utf-16-le') as fp:   
        for item in results:
            v = item['Voice']
            if v:
                fp.write(f"{v}.ogg\n")

if __name__ == '__main__':
    cmd = parse_args()
    main(cmd.JA, cmd.op, cmd.ft)