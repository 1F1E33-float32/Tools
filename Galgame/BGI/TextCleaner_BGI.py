import re
import json
import argparse
from glob import glob

import TextCleaner_BGI_C

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-ve", type=int, default=1)
    return parser.parse_args(args=args, namespace=namespace)

def get_code_section(code_section):
    code_bytes, text_bytes, config = TextCleaner_BGI_C.split_data(code_section)
    text_section = TextCleaner_BGI_C.get_text_section(text_bytes)
    code_section = TextCleaner_BGI_C.get_code_section(code_bytes, text_section, config)
    return code_section

def text_cleaning(text):
    text = re.sub(r'\uf8f3|\u0002|\u0001', "", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.replace('「', '').replace('」', '').replace('（', '').replace('）', '').replace('『', '').replace('』', '')
    text = text.replace('　', '').replace('\n', '')
    return text

def process_type0(code_section, results):
    for index, item in enumerate(code_section):
        if item == ('OTHER', '_PlayVoice'):
            Voice = code_section[index - 1][1].lower()
            for i in range(index, len(code_section)):
                if code_section[i][0] == 'NAME':
                    Speaker = code_section[i][1]
                    Speaker = Speaker.split("／")[-1].replace("＠", "")
                elif code_section[i][0] == 'TEXT':
                    Text = text_cleaning(code_section[i][1])
                    results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
                    break

def process_type1(code_section, results):
    pass
    for item in code_section:
        pass

def process_type2(code_section, results):
    for item in code_section:
        pass

PROCESSORS = {
    0:   process_type0,
    1:   process_type1,
    2:   process_type2,
}

def main(JA_dir, op_json, version):
    processor = PROCESSORS[version]
    filelist = glob(f"{JA_dir}/**/*", recursive=True)
    results = []

    for fn in filelist:
        with open(fn, 'rb') as f:
            data = f.read()
        code_section = get_code_section(data)
        clean_code_section = [item for item in code_section.values() if 'bs5' not in item[1]]

        temp = []
        processor(clean_code_section, temp)
        if not temp:
            continue
        results.extend(temp)

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

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op, args.ve)