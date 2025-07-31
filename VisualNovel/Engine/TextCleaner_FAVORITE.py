import re
import json
import argparse
from tqdm import tqdm
from glob import glob

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"E:\Games\Galgame\FAVORITE\Sakura, Moyu. -as the Night's, Reincarnation-")
    parser.add_argument("-op", type=str, default=r'D:\AI\Audio_Tools\python\1.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\[(\w+)\|\w+\]', r'\1', text)
    text = re.sub(r'\[・\|(\w+)\]', r'\1', text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '')
    return text

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/script.txt", recursive=True)
    results = []
    
    for file_name in filelist:
        with open(file_name, 'r', encoding='cp932') as file:
            script = file.read()
            script = re.sub(r'	neg\n', '', script)

        segments = script.split('# =================================================')

        results_spk = {}
        speak_mapping = {}
        speak_pushstring = {}

        for segment in segments:
            segment = segment.strip()
            match = re.match(r'(SPEAK_\d+_):', segment)
            if match:
                speak_id = match.group(1)
                pushstrings = re.findall(r'pushstring\s+(.*)', segment)
                if pushstrings:
                    last_pushstring = pushstrings[-1]
                    last_pushstring = last_pushstring.replace('　', '').replace(' ', '')
                    speak_pushstring[speak_id] = last_pushstring
                
                calls = re.findall(r'call\s+(SPEAK_\d+_)', segment)
                for call in calls:
                    speak_mapping[speak_id] = call
        results_spk = {**speak_pushstring, **{key: speak_pushstring[val] for key, val in speak_mapping.items() if val in speak_pushstring}}

        pattern_1 = re.compile(r'^.*pushint.*\r?\n.*pushtrue rep.*\r?\n.*call SPEAK_.*\r?\n.*pushstring.*$', re.MULTILINE)
        matches_1 = pattern_1.findall(script)
        pattern_2 = re.compile(r'^.*pushint.*\r?\n.*pushint.*\r?\n.*pushtrue\b\r?\n.call SPEAK_.*\r?\n.*pushstring.*$', re.MULTILINE)
        matches_2 = pattern_2.findall(script)
        
        for match in matches_1:
            parts = match.split('\n')
            cleaned_parts = [part.lstrip('\t') for part in parts]
            for i, part in enumerate(cleaned_parts):
                if i == 0:
                    Voice = re.search(r'pushint\s+(\d+)', part).group(1)
                elif i == 2:
                    Speaker = re.search(r'call\s(SPEAK_\d+_)', part).group(1)
                    Speaker = results_spk.get(Speaker, None)
                elif i == 3:
                    Text = re.search(r'pushstring\s+(.+)', part).group(1)
                    Text = text_cleaning(Text)
            results.append((Speaker, Voice, Text))

        for match in matches_2:
            parts = match.split('\n')
            cleaned_parts = [part.lstrip('\t') for part in parts]
            for i, part in enumerate(cleaned_parts):
                if i == 0:
                    Voice = re.search(r'pushint\s+(\d+)', part).group(1)
                elif i == 3:
                    Speaker = re.search(r'call\s(SPEAK_\d+_)', part).group(1)
                    Speaker = results_spk.get(Speaker, None)
                elif i == 4:
                    Text = re.search(r'pushstring\s+(.+)', part).group(1)
                    Text = text_cleaning(Text)
            results.append((Speaker, Voice, Text))

    with open(op_json, mode='w', encoding='utf-8') as file:
        json_data = [{'Speaker': Speaker, 'Voice': Voice.zfill(8), 'Text': Text} for Speaker, Voice, Text in tqdm(results)]
        json.dump(json_data, file, ensure_ascii=False, indent=4)
    
if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)