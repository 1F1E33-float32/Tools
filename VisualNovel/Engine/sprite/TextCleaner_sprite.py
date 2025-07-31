import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r'E:\Games\Galgame\sprite\Ao no Kanata no Four Rhythm\Aokana_Data\system_ext\scripts')
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '').replace('“', '').replace('”', '').replace('≪', '').replace('≫', '')
    text = text.replace('\n', '').replace(r'\n', '').replace(r'　', '').replace('♪', '').replace('♥', '').replace('%r', '')
    return text

def read_bs5(JA_dir, op_json):
    files_original = glob(f"{JA_dir}/**/*.bs5", recursive=True)
    result = []
    seen = set()
    for filename in tqdm(files_original):
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
        
        i = 0
        j = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("voice0"):
                elements1 = line.split('\t')
                if len(elements1) == 2:
                    Voice = elements1[1].split('//')[0]
                    if i < len(lines) and Voice not in seen:
                        seen.add(Voice)
                        for j in range(i + 1, len(lines)):
                            next_line = lines[j]
                            if (not next_line.startswith("//")) and (not next_line.startswith("@")):
                                try:
                                    elements2 = next_line.split('␂')[2].split('：')
                                    Speaker = elements2[0].replace('【', '').replace('】', '')
                                    Text = elements2[1]
                                    Text = text_cleaning(Text)
                                    result.append((Speaker, Voice, Text))
                                    break
                                except:
                                    break
            i += 1

    with open(op_json, mode='w', encoding='utf-8') as file:
        json_data = [{'Speaker': Speaker, 'Voice': Voice, 'Text': Text} for Speaker, Voice, Text in result]
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    read_bs5(args.JA, args.op)