import regex as re
import os
import json
import argparse
from glob import glob

from TextCleaner_YuRis_YSTL import YSTL
from TextCleaner_YuRis_YSCM import YSCM
from TextCleaner_YuRis_YSTB import YSTB

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-vm", type=str, default=r"D:\Fuck_galgame\ysbin")
    parser.add_argument("-sc", type=str, default=r"D:\Fuck_galgame\scenario")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-md", type=int, default=1)
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\\[a-zA-Z]', '', text)
    text = re.sub(r"＠{1,}", "。", text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace(' ', '').replace('♪', '').replace('//', '').replace('☆', '').replace('▼', '')
    text = re.sub(r'≪([^／≫]+)／[^≫]+≫', r'\1', text)
    return text

def main_txt(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**.txt", recursive=True)
    results = []
    seen = set()
    for filename in filelist:
        with open(filename, encoding='cp932') as f:
            lines = f.readlines()
        for lines in lines:
            match = re.match(r'\\VO\(([^)]+)\)\(([^)]+)\)【([^】]+)】(.+)', lines)
            if match:
                Voice = match.group(1)
                if Voice in seen:
                    continue
                Speaker = match.group(3).split('＠')[0]
                seen.add(Voice)
                if Speaker == None or Voice == None or match.group(4) == None:
                    print(f"Error: {filename}")
                    continue
                results.append({'Speaker': Speaker, 'Voice': Voice.lower(), 'Text': text_cleaning(match.group(4))})
            match = re.match(r'\\VO\(([^)]+)\)【([^】]+)】(.+)', lines)
            if match:
                Voice = match.group(1)
                Voice = Voice.replace('\t', '')
                if Voice in seen:
                    continue
                Speaker = match.group(2).split('＠')[0]
                seen.add(Voice)
                if Speaker == None or Voice == None or match.group(3) == None:
                    print(f"Error: {filename}")
                    continue
                results.append({'Speaker': Speaker, 'Voice': Voice.lower(), 'Text': text_cleaning(match.group(3))})

    with open(op_json, mode='w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

def main_vm_w(VM_dir, op_json):
    yst_list = glob(f"{VM_dir}/yst_list.ybn", recursive=True)[0]
    ysc = glob(f"{VM_dir}/ysc.ybn", recursive=True)[0]
    filelist = YSTL(yst_list)
    op, id = YSCM(ysc)
    result = []
    seen = set()
    for file in filelist:
        print(file)
        file = os.path.join(VM_dir, file)
        voice_list, text_list = YSTB(file, op, id)
        for Voice, text in zip(voice_list, text_list):
            if Voice in seen:
                continue
            seen.add(Voice)
            match 0:
                case 0:
                    a = re.match(r"【(.*?)】(.*)", text)
                    if not a:
                        continue
                case 1:
                    for pattern in [r"(.*)【(.*?)】", r"(.*)『(.*?)』", r"(.*)「(.*?)」"]:
                        a = re.match(pattern, text)
            if a:
                Speaker = a.group(1)
                Speaker = Speaker.split('＠')[0]
                Speaker = Speaker.split('／')[-1]
                Text = a.group(2)
                Text = text_cleaning(Text)
                result.append({'Speaker': Speaker, 'Voice': Voice.lower(), 'Text': Text})
            
    with open(op_json, mode='w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)

def main_vm_c(VM_dir, op_json):
    yst_list = glob(f"{VM_dir}/yst_list.ybn", recursive=True)[0]
    ysc = glob(f"{VM_dir}/ysc.ybn", recursive=True)[0]
    filelist = YSTL(yst_list)
    op, id = YSCM(ysc)
    result = []
    seen = set()

    pattern = r'''
    ^(\S+)               # 捕获前缀，至少一个非空白字符
    (?P<bracket>[『「（])  # 捕获开括号，命名为 'bracket'
    (?P<content>         # 捕获内容，命名为 'content'
        (?:
            [^『「（』」）]+  # 非括号字符
            |
            (?&bracket)  # 递归匹配相同类型的开括号
            (?&content)  # 递归匹配内容
            [』」）]      # 匹配相应的闭括号
        )*
    )
    [』」）]$               # 匹配闭括号并确保在字符串结尾
    '''
    a_re = re.compile(pattern, re.VERBOSE)
    for file in filelist:
        print(file)
        file = os.path.join(VM_dir, file)
        voice_list, text_list = YSTB(file, op, id)
        for Voice, text in zip(voice_list, text_list):
            if text.startswith('“') or text.endswith('。'):
                continue
            if Voice in seen:
                continue
            seen.add(Voice)
            text = text_cleaning(text)
            a = a_re.match(text)
            if a:
                Speaker = a.group(1)
                Speaker = Speaker.split('／')
                if len(Speaker) > 1:
                    Speaker = Speaker[1]
                else:
                    Speaker = Speaker[0]
                Speaker = Speaker.replace('【', '').replace('】', '')
                Text = a.group('content')
                Text = text_cleaning(Text)
                result.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
    with open(op_json, mode='w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    match args.md:
        case 0:
            main_txt(args.sc, args.op)
        case 1:
            main_vm_w(args.vm, args.op)
        case 2:
            main_vm_c(args.vm, args.op)