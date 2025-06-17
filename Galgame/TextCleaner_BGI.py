import re
import os
import json
import argparse
from glob import glob

import TextCleaner_BGI_C

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-vo", type=str, default=r'D:\Fuck_galgame\voice')
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-ve", type=int, default=1)
    return parser.parse_args(args=args, namespace=namespace)

class Check_Spk():
    def __init__(self, Voice_path):
        self.audio_files = {}
        for root, dirs, files in os.walk(Voice_path):
            for file in files:
                self.audio_files[file.lower()] = os.path.join(root, file)
    def check(self, Voice):
        if Voice.lower() in self.audio_files:
            return True
        else:
            return False

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

def main(JA_dir, voice_path, op_json, version):
    check = Check_Spk(voice_path)
    filelist = glob(f"{JA_dir}/**/*", recursive=True)
    results = []

    for filename in filelist:
        with open(filename, 'rb') as file:
            data = file.read()
            code_section = get_code_section(data)
        print(filename)
        for index in code_section:
            continue
            match version:
                case 0:
                    '''
                    -1 = ('OTHER', 'Voice')
                     0 = ('NAME', 'Speaker')
                     1 = ('TEXT', 'Text')
                    '''
                    if index != 0 and code_section[index][0] == "NAME" and code_section[index - 1][0] == "OTHER" and code_section[index + 1][0] == "TEXT":
                        Speaker = code_section[index][1].replace(' ', '')
                        Voice = code_section[index - 1][1]
                        Text = code_section[index + 1][1]
                        if not check.check(Voice):
                            print(f"Voice {Voice} not found")
                            continue
                        #pattern = re.compile(r'^([A-Za-z]+)\d+')
                        #Speaker_id = pattern.match(Voice).group(1)
                        Speaker_id = Voice.split('_')[0]
                        Text = text_cleaning(Text)
                        results.append((Speaker, Speaker_id, Voice, Text))
                case 1:
                    '''
                    -1 = ('OTHER', 'Voice')
                     0 = ('OTHER', 'Speaker')
                     1 = ('TEXT BACKLOG', 'Text')
                    '''
                    if index != 0 and code_section[index][0] == "TEXT BACKLOG" and code_section[index - 1][0] == "OTHER" and code_section[index - 2][0] == "OTHER":
                        Text = code_section[index][1]
                        Speaker = code_section[index - 1][1].replace(' ', '')
                        Voice = code_section[index - 2][1]
                        if not check.check(Voice):
                            print(f"Voice {Voice} not found")
                            continue
                        #pattern = re.compile(r'^([A-Za-z]+)\d+')
                        #Speaker_id = pattern.match(Voice).group(1)
                        Speaker_id = Voice.split('_')[0]    
                        Text = text_cleaning(Text)
                        results.append((Speaker, Speaker_id, Voice, Text))
                case 2:
                    if code_section[index][0] == "NAME" and index != 0:
                        if code_section[index - 2][0] == "OTHER" and code_section[index - 1][0] == "OTHER" and code_section[index - 1][1] == "Voice":
                            Speaker = code_section[index][1]
                            Voice = code_section[index - 2][1]
                            Text = code_section[index + 1][1]

                            Text = text_cleaning(Text)
                            results.append((Speaker, Voice, Text))
                case 3:
                   if code_section[index][0] == "NAME" and index != 0:
                        if code_section[index - 1][0] == "OTHER" and code_section[index - 1][1] == "_PlayVoice" and code_section[index - 2][0] == "OTHER":
                            Speaker = code_section[index][1]
                            Voice = code_section[index - 2][1]
                            Text = code_section[index + 1][1]
                            if not check.check(Voice):
                                print(f"Voice {Voice} not found")
                                continue
                            Text = text_cleaning(Text)
                            results.append((Speaker, Voice, Text))
        
    match version:
        case 0:
            replace_dict = {}
            for Speaker, Speaker_id, Voice, Text in results:
                if (Speaker != '？' and Speaker != '？？？' and Speaker != '\u3000') and Speaker_id not in replace_dict:
                    replace_dict[Speaker_id] = Speaker

            results_fix = []
            for Speaker, Speaker_id, Voice, Text in results:
                if (Speaker == '？' or Speaker == '？？？' or Speaker == '\u3000') and Speaker_id in replace_dict:
                    results_fix.append((replace_dict[Speaker_id], Voice, Text))
                else:
                    results_fix.append((Speaker, Voice, Text))

    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results_fix:
            if Voice not in seen:
                seen.add(Voice)
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.vo, args.op, args.ve)