import re
import os
import random
from glob import glob
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn

rich_progress = Progress(TextColumn("Preprocess:"), BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%", "•", MofNCompleteColumn(), "•", TimeElapsedColumn(), "|", TimeRemainingColumn())

def Genshin_ZH_clean(text, wav_name):
    PRONOUN_DICT = {
        "INFO_MALE_PRONOUN_UNCLE": "叔叔",
        "INFO_MALE_PRONOUN_BIGBROTHER": "大哥哥",   
        "INFO_MALE_PRONOUN_SISTER": "妹妹",
        "INFO_MALE_PRONOUN_CUTEBIGBROTHER": "大葛格",
        "INFO_MALE_PRONOUN_BOY": "少年",
        "INFO_MALE_PRONOUN_BOYA": "小哥",
        "INFO_MALE_PRONOUN_BOYC": "先生",
        "INFO_MALE_PRONOUN_BOYD": "王子",
        "INFO_MALE_PRONOUN_BOYE": "小伙子",
        "INFO_MALE_PRONOUN_GIRLD": "公主",
        "INFO_MALE_PRONOUN_HERO": "男一号",
        "INFO_MALE_PRONOUN_SHE": "她",
        "INFO_MALE_PRONOUN_YING": "荧",
        "INFO_MALE_PRONOUN_HE": "他",
        "INFO_MALE_PRONOUN_BROANDSIS": "哥哥姐姐",
        "INFO_MALE_PRONOUN_BROTHER": "哥哥",
        "INFO_MALE_PRONOUN_XIABOY": "少侠",
        "INFO_MALE_PRONOUN_Twins2Male": "这也是我妹妹头上的花。",
        "INFO_FEMALE_PRONOUN_AUNT": "阿姨",
        "INFO_FEMALE_PRONOUN_BIGSISTER": "大姐姐",
        "INFO_FEMALE_PRONOUN_BROTHER": "哥哥",
        "INFO_FEMALE_PRONOUN_CUTEBIGSISTER": "大捷洁",
        "INFO_FEMALE_PRONOUN_GIRL": "少女",
        "INFO_FEMALE_PRONOUN_GIRLA": "老妹",
        "INFO_FEMALE_PRONOUN_GIRLB": "姑娘",
        "INFO_FEMALE_PRONOUN_GIRLC": "小姐",
        "INFO_FEMALE_PRONOUN_GIRLD": "公主",
        "INFO_FEMALE_PRONOUN_GIRLE": "小姑娘",
        "INFO_FEMALE_PRONOUN_BOYD": "王子",
        "INFO_FEMALE_PRONOUN_HEROINE": "女一号",
        "INFO_FEMALE_PRONOUN_HE": "他",    
        "INFO_FEMALE_PRONOUN_KONG": "空",
        "INFO_FEMALE_PRONOUN_SHE": "她",
        "INFO_FEMALE_PRONOUN_SISANDSIS": "两位姐姐",
        "INFO_FEMALE_PRONOUN_SISTER": "妹妹",
        "INFO_FEMALE_PRONOUN_SISTERA": "姐姐",
        "INFO_FEMALE_PRONOUN_XIAGIRL": "女侠",
        "INFO_FEMALE_PRONOUN_YING": "荧",
        "INFO_FEMALE_PRONOUN_Twins2Female": "这种花自我苏醒便戴在我的头上。",
    }
    #不按套路出牌的，先抢救他她，后面的全部送走
    text = re.sub(r"\{PLAYERAVATAR#SEXPRO\[INFO_MALE_PRONOUN_HE\|INFO_MALE_PRONOUN_SHE\]\}", random.choice(['他', '她']), text)
    text = re.sub(r"\{PLAYERAVATAR#SEXPRO\[INFO_MALE_PRONOUN_SHE\|INFO_MALE_PRONOUN_HE\]\}", random.choice(['他', '她']), text)
    if re.findall(r'\{PLAYERAVATAR#SEXPRO\[INFO_MALE_PRONOUN_[A-Z]+\|INFO_MALE_PRONOUN_[A-Z]+\]\}', text) != []:
        return ''
    #按套路出牌的
    polaritys = re.findall(r"\b(PLAYERAVATAR|MATEAVATAR)\b", text)
    if len(polaritys) != 0 and 'hero' not in wav_name.lower() and 'heroine' not in wav_name.lower() and ('a.wav' in wav_name.lower() or 'b.wav' in wav_name.lower()): #过滤器，必须有a.wav或b.wav，且不是主角
        for polarity in polaritys:
            if polarity == 'PLAYERAVATAR' and wav_name.lower().endswith("a.wav"):
                target_pattern = re.findall(r'INFO_MALE_PRONOUN_[A-Z]+', text)[0]
            elif polarity == 'PLAYERAVATAR' and wav_name.lower().endswith("b.wav"):
                target_pattern = re.findall(r'INFO_FEMALE_PRONOUN_[A-Z]+', text)[0]
            elif polarity == 'MATEAVATAR' and wav_name.lower().endswith("a.wav"):
                target_pattern = re.findall(r'INFO_FEMALE_PRONOUN_[A-Z]+', text)[0]
            elif polarity == 'MATEAVATAR' and wav_name.lower().endswith("b.wav"):
                target_pattern = re.findall(r'INFO_MALE_PRONOUN_[A-Z]+', text)[0]
            replace = PRONOUN_DICT[target_pattern]
            replace_full = re.findall(r"\{[^#]*#SEXPRO\[[^\|]+\|[^\]]+\]\}", text)
            text = re.sub(re.escape(replace_full[0]), replace, text, count=1)
    #没有a.wav或b.wav标识，导致无法判断性别的,然后又有#SEXPRO标记的，先抢救他她，后面的全部送走
    text = re.sub(r"\{PLAYERAVATAR#SEXPRO\[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE\]\}", random.choice(['他', '她']), text)
    if re.findall(r"\{[^#]*#SEXPRO\[[^\|]+\|[^\]]+\]\}", text) != []:
        return ''
    return text

def Universal_Clean(text, wav_name):
    if wav_name.lower().endswith("a.wav") or wav_name.lower().endswith("_m.wav"):
        text = re.sub(r"\{F#[^}]*\}\{M#([^}]*)\}", r"\1", text)
        text = re.sub(r"\{M#([^}]*)\}\{F#[^}]*\}", r"\1", text)
    elif wav_name.lower().endswith("b.wav") or wav_name.lower().endswith("_f.wav"):
        text = re.sub(r"\{F#([^}]*)\}\{M#[^}]*\}", r"\1", text)
        text = re.sub(r"\{M#[^}]*\}\{F#([^}]*)\}", r"\1", text)
    #没有a.wav或b.wav标识，导致无法判断性别的,然后又有{M#他}{F#她}标记的
    text = re.sub(r'\{(M|F)#(他|她)\}', random.choice(['他', '她']), text)
    text = re.sub(r'\{(M|F)#(他们|她们)\}', random.choice(['他们', '她们']), text)
    #玩七圣召唤玩的
    if re.findall(r'\{SPRITE_PRESET#(\d+)\}', text) != []:
        return ''
    text = re.sub(r'\{RUBY_[^}]+\}|\{RUBY#[^}]+\}|<[^>]+>|\$UNRELEASED', '', text)
    text = re.sub(r'^#', '', text)
    #就你天天介绍天才俱乐部的席位是吧
    if re.findall(r'#\d+', text) != []:
        return ''
    return text

def process_lab_text(lab_file, wav_file):
    with open(lab_file, 'r', encoding='utf-8') as lab:
        lab_text = lab.read()
    #这三个直接放弃，“难得呀，要不要去飞一飞？”这句会把chinese.py淦懵逼
    if '{NICKNAME}' in lab_text or '{TEXTJOIN#54}' in lab_text or '难得呀，要不要去飞一飞？'in lab_text:
        return '', lab_text
    else:
        lab_text_clean = Genshin_ZH_clean(lab_text, wav_file)
        lab_text_clean = Universal_Clean(lab_text, wav_file)
    return lab_text_clean, lab_text

def main(input_dir):
    main = rich_progress.add_task("Preprocess", total=len(os.listdir(input_dir)))
    with rich_progress:
        for subdir in os.listdir(input_dir):
            subdir_path = os.path.join(input_dir, subdir)
            lab_files = glob(os.path.join(subdir_path, '*.lab'))
            for lab_file in lab_files:
                wav_file = lab_file.replace('.lab', '.wav')
                if not os.path.exists(wav_file):
                    os.remove(lab_file)
                    continue
                processed_lab_text, lab_text = process_lab_text(lab_file, wav_file)
                if processed_lab_text == '':
                    os.remove(lab_file)
                    print(f'{lab_file} is removed')
                    os.remove(wav_file)
                    print(f'{wav_file} is removed')
                else:
                    os.remove(lab_file)
                    with open(os.path.join(subdir_path, lab_file.replace('.lab', '.txt')), 'a', encoding='utf-8') as lab_file:
                        lab_file.write(f'{processed_lab_text}')
                    with open(os.path.join(input_dir, "debug.txt"), 'a', encoding='utf-8') as debug_file:
                        debug_file.write(f'{lab_text}\n')
                        debug_file.write(f'{processed_lab_text}\n')
            rich_progress.update(main, advance=1)

if __name__ == '__main__':
    main(r'D:\1\mihoyo_CN_4.3_1.6')