import re
import json
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\sc")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace('\\n', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.wsc", recursive=True)
    speaker_start = False
    text_start = False
    results = []
    for filename in tqdm(filelist):
        with open(filename, 'rb') as file:
            data = file.read()

        i = 0
        while i < len(data):
            if data[i: i + 2] == b'\x65\x00' and all(data[i + 2 + a] != 0x00 for a in range(3)):
                i += 2
                segment = bytearray()
                while i < len(data) and data[i] != 0:
                    segment.append(data[i])
                    i += 1
                Voice = segment.decode('cp932')
                if Voice == '':
                    pass
                Speaker_id = Voice.split('_')[0]
                speaker_start = True

            if data[i: i + 2] == b'\x0F\x0F' and speaker_start:
                i += 2
                segment = bytearray()
                while i < len(data) and data[i] != 0:
                    segment.append(data[i])
                    i += 1
                Speaker = segment.decode('cp932')
                Speaker = Speaker.split('／')[-1]
                speaker_start = False
                text_start = True

            if data[i: i + 1] == b'\x00' and text_start:
                i += 1
                segment = bytearray()
                while i < len(data) and data[i: i + 1] != b'%':
                    segment.append(data[i])
                    i += 1
                Text = segment.decode('cp932')
                Text = text_cleaning(Text)
                results.append((Speaker, Speaker_id, Voice, Text))
                text_start = False

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