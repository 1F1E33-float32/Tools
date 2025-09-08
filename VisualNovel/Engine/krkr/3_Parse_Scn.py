import re
import json
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\scn")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-ol", type=str, default=r'D:\Fuck_galgame\files.txt')
    parser.add_argument("-ot", type=str, default=r'D:\Fuck_galgame\appconfig.tjs')  # 新增：输出 tjs
    parser.add_argument("-ft", type=int, default=2)
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

'''
0 = '沙里'
1 = [['？？？', '「案内係なんでしょ」', 10], ['???', '"You\'re a guide, right?"', 24], ['？？？', '「你是向导吧？」', 8], ['？？？', '「你是嚮導吧？」', 8]]
2 = [{'name': '沙里', 'pan': 0, 'type': 0, 'voice': 'sari_0001'}]
3 = 192
4 = ...
'''
def process_type0(_0_JA_data, results):
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

def process_type1(_0_JA_data, results):
    if 'scenes' in _0_JA_data:
        for _1_JA_scenes in _0_JA_data['scenes']:
            if 'texts' in _1_JA_scenes:
                for _2_JA_texts in _1_JA_scenes['texts']:
                    Speaker = Voice = Text = None
                    if _2_JA_texts[3] is not None:
                        Speaker = _2_JA_texts[3][0]['name']
                        Voice = _2_JA_texts[3][0]['voice'].lower()

                    Text = text_cleaning(_2_JA_texts[2])

                    results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})

'''
0 = 'ショコラ'
1 = None
2 = [[None, '「お、おはよう……ござい、ます……」'], ['Chocola', '「G-Good morning... to you...」'], ['巧克力', '「早、早安……」']]
3 = [{'name': 'ショコラ', 'pan': 0, 'type': 0, 'voice': 'A_01_001'}]
4 = 1744
5 = ...
'''
def process_type2(_0_JA_data, results):
    if 'scenes' in _0_JA_data:
        for _1_JA_scenes in _0_JA_data['scenes']:
            if 'texts' in _1_JA_scenes:
                for _2_JA_texts in _1_JA_scenes['texts']:
                    Speaker = Voice = Text = None
                    if _2_JA_texts[3] is not None:
                        Speaker = _2_JA_texts[3][0]['name']
                        Voice = _2_JA_texts[3][0]['voice'].lower()

                    Text = text_cleaning(_2_JA_texts[2][0][1])

                    results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})

PROCESSORS = {
    0: process_type0,
    1: process_type1,
    2: process_type2,
}

def write_appconfig_tjs(results, tjs_path):
    voices = [item['Voice'] for item in results if item.get('Voice')]
    lines = []
    for v in voices:
        lines.append("try")
        lines.append("{")
        lines.append(f'Scripts.evalStorage("{v}.ogg");')
        lines.append("}")
        lines.append("catch{}")
        lines.append("")
    content = "\n".join(lines).rstrip() + "\n"

    with open(tjs_path, 'w', encoding='utf-8-sig') as fp:
        fp.write(content)

def main(JA_dir, op_json, ol, ot, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = [fn for fn in glob(f"{JA_dir}/**/*.json", recursive=True) if not fn.lower().endswith(".resx.json")]

    results = []
    for fn in tqdm(filelist):
        data = read_json_file(fn)
        processor(data, results)
        if not results:
            continue

    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(op_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    with open(ol, 'w', encoding='utf-16-le') as fp:
        for item in results:
            v = item['Voice']
            if v:
                fp.write(f"{v}.ogg\n")

    write_appconfig_tjs(results, ot)

if __name__ == '__main__':
    cmd = parse_args()
    main(cmd.JA, cmd.op, cmd.ol, cmd.ot, cmd.ft)