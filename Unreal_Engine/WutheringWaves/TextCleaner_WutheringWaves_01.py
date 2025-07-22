import re
import os
import json
import struct
import sqlite3
import inspect
import argparse
from tqdm import tqdm

from Aki.FavorWord import FavorWord
from Aki.FlowState import FlowState

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_flowState", type=str, default=r"D:\Dataset_Game\WutheringWaves\Client\Content\Aki\ConfigDB\db_flowState.db")
    parser.add_argument("--lang_multi_text", type=str, default=r"D:\Dataset_Game\WutheringWaves\Client\Content\Aki\ConfigDB\zh-Hans\lang_multi_text.db")
    parser.add_argument("--db_favor", type=str, default=r"D:\Dataset_Game\WutheringWaves\Client\Content\Aki\ConfigDB\db_favor.db")

    parser.add_argument("--au", type=str, default=r"D:\Dataset_Game\WutheringWaves\Client\Content\Aki\WwiseAudio_Generated\Event\zh")
    parser.add_argument("--op", type=str, default=r"D:\Dataset_Game\WutheringWaves\EXP")

    parser.add_argument("--md", type=str, default="zh")
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    global mode
    if mode == "zh" or mode =="jp":
        text = text.replace('{PlayerName}', '漂泊者')
    elif mode == "en":
        text = text.replace('{PlayerName}', 'Rover')
    elif mode == "ko":
        text = text.replace('{PlayerName}', '방랑자')
    text = text.replace('（', '').replace('）', '').replace('(', '').replace(')', '').replace('「', '').replace('」', '').replace('"', '')
    text = text.replace('\r', '').replace('\n', '')
    text = re.sub(r'<color=[^>]+>(.*?)<\/color>', r'\1', text)
    text = re.sub(r"<.*?>", '', text)
    text = text.replace('<', '')
    return text

def name_mappping(id):
    id = int(id)
    global mode
    if mode == "zh" or mode =="jp":
        if id == 1501 or id == 1604 or id == 1406:
            return "漂泊者_男"
        elif id == 1502 or id == 1605 or id == 1408:
            return "漂泊者_女"
        elif id == 83 or id == 354:
            return ["漂泊者_男", "漂泊者_女"]
        
    elif mode == "en":
        if id == 1501 or id == 1604 or id == 1406:
            return "Rover_male"
        elif id == 1502 or id == 1605 or id == 1408:
            return "Rover_female"
        elif id == 83 or id == 354:
            return ["Rover_male", "Rover_female"]
        
    elif mode == "ko":
        if id == 1501 or id == 1604 or id == 1406:
            return "방랑자_남성"
        elif id == 1502 or id == 1605 or id == 1408:
            return "방랑자_여성"
        elif id == 83 or id == 354:
            return ["방랑자_남성", "방랑자_여성"]
        
def _convert_value(v):
    if hasattr(v, "Init") or hasattr(v, "_tab"):
        return fb_to_dict(v)
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="ignore")
    return v

def fb_to_dict(obj):
    result = {}
    seen = set()

    for name, fn in inspect.getmembers(obj, predicate=callable):
        if name.startswith('_') or name.endswith('Length') or name in seen:
            continue
        try:
            if inspect.signature(fn).parameters:
                continue
        except (ValueError, TypeError):
            continue

        length_fn = getattr(obj, name + "Length", None)
        if callable(length_fn):
            ln = length_fn()
            arr = []
            for i in range(ln):
                v = fn(i)
                arr.append(_convert_value(v))
            result[name] = arr
            seen.add(name)
            continue

        v = fn()
        result[name] = _convert_value(v)
        seen.add(name)

    return result

def extract_talk_items(data):
    result = []
    for dictionary_A in data:
        if dictionary_A.get("Name") == "ShowTalk":
            talk_items = dictionary_A.get("Params", {}).get("TalkItems", [])
            for dictionary_B in talk_items:
                result.append({"TidTalk": dictionary_B.get("TidTalk"), "WhoId": dictionary_B.get("WhoId")})
    return result

def process_flowstate(cursor_flowstate, lang_dict):
    cursor_flowstate.execute("SELECT binData FROM flowstate")
    bin_datas = cursor_flowstate.fetchall()

    result = []

    for bin_data in tqdm(bin_datas, ncols=150):
        fw = FlowState.GetRootAsFlowState(bin_data[0], 0)
        data = fb_to_dict(fw)
        json_data = json.loads(data["Actions"])
        extracted_items = extract_talk_items(json_data)
        for item in extracted_items:
            tid_talk = item["TidTalk"]
            talk_text = lang_dict.get(tid_talk)
            if not talk_text or not tid_talk:
                continue
            
            talk_text = text_cleaning(talk_text)

            who_id = item["WhoId"]
            if who_id == 83 or who_id == 354:
                result.append({"WhoId": name_mappping(who_id)[0], "Text": talk_text, "TidTalk": tid_talk + "_M"})
                result.append({"WhoId": name_mappping(who_id)[1], "Text": talk_text, "TidTalk": tid_talk + "_F"})
            else:
                speaker_name = lang_dict.get(f"Speaker_{who_id}_Name")
                speaker_name = speaker_name if speaker_name else "None"
                speaker_name = speaker_name.replace('"', '').replace(':', '')
                sex_pattern = r"\{Male=(.*?);Female=(.*?)\}"
                match_sex = re.search(sex_pattern, talk_text)
                if match_sex:
                    male_value = match_sex.group(1)
                    female_value = match_sex.group(2)
                    result_with_male = re.sub(sex_pattern, male_value, talk_text)
                    result_with_female = re.sub(sex_pattern, female_value, talk_text)
                    result.append({"WhoId": speaker_name, "Text": result_with_male,   "TidTalk": tid_talk + "_M"})
                    result.append({"WhoId": speaker_name, "Text": result_with_female, "TidTalk": tid_talk + "_F"})
                    continue
                result.append({"WhoId": speaker_name, "Text": talk_text, "TidTalk": tid_talk})
    return result

def get_bnk(file_path):
    with open(file_path, 'rb') as file:
        file.seek(56)
        
        num_blocks_bytes = file.read(4)
        num_blocks = struct.unpack('<I', num_blocks_bytes)[0]
        
        blocks = []
        for i in range(num_blocks):
            Chunk_Type = struct.unpack('B', file.read(1))[0]

            Chunk_Size_bytes = file.read(4)
            Chunk_Size = struct.unpack('<I', Chunk_Size_bytes)[0]
            
            block_data = file.read(Chunk_Size)
            
            if Chunk_Type == 0x02:
                if Chunk_Size >= 9:
                    offset = 9
                    Source_ID_bytes = block_data[offset:offset + 4]
                    Source_ID = struct.unpack('<I', Source_ID_bytes)[0]
                blocks.append({'SourceID': Source_ID})
        
        return blocks

def find_file(file_name, start_dir):
    for root, dirs, files in os.walk(start_dir):
        if file_name in files:
            return os.path.join(root, file_name)

def get_favorword(cursor_favorword):
    cursor_favorword.execute("SELECT BinData FROM favorword")
    rows = cursor_favorword.fetchall()

    result = []
    for row in rows:
        fw = FavorWord.GetRootAsFavorWord(row[0], 0)
        data = fb_to_dict(fw)

        Content = data['Content']
        Voice = data['Voice']
        Voice = Voice.split('.')[-1]

        result.append({"function_names": Content, "function_favorwords": Voice})
    return result

def process_favorword(cursor_favorword, lang_dict, au):
    results = []

    favorwords = get_favorword(cursor_favorword)
    for favorword in tqdm(favorwords, ncols=150):
        function_name = favorword["function_favorwords"] + ".bnk"
        function_favorword = favorword["function_names"]
        role_id = function_favorword.split("_")[1][:4]
        if role_id in ["1501", "1502", "1604", "1605", "1406", "1408"]: # 衍射，湮灭，气动
            Whoid = name_mappping(role_id)
        else:
            Whoid = lang_dict.get(f"RoleInfo_{role_id}_Name")

        file_name = find_file(function_name, au)
        wwise_short_name = get_bnk(file_name)
        if len(wwise_short_name) != 1:
            print(f"\n{function_name}, {wwise_short_name}")
        wwise_short_name = wwise_short_name[0]["SourceID"]

        text = lang_dict.get(function_favorword)
        if text =='（语气词）':
            continue
        text = text_cleaning(text)

        results.append({"WhoId": Whoid, "Text": text, "TidTalk": wwise_short_name})

    return results

def load_multitext_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT Id, Content FROM MultiText")
    data = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return data

if __name__ == "__main__":
    global mode
    args = parse_args()
    mode = args.md

    # 1) Load lang table once
    lang_dict = load_multitext_db(args.lang_multi_text)

    # 2) Open other DBs
    conn_flowstate = sqlite3.connect(args.db_flowState)
    cursor_flowstate = conn_flowstate.cursor()

    conn_favorword = sqlite3.connect(args.db_favor)
    cursor_favorword = conn_favorword.cursor()

    # 3) Process using dict lookups
    extracted_flowstate = process_flowstate(cursor_flowstate, lang_dict)
    extracted_favorword = process_favorword(cursor_favorword, lang_dict, args.au)

    # 4) Close the remaining DBs
    conn_flowstate.close()
    conn_favorword.close()

    final_index = extracted_favorword + extracted_flowstate

    with open(args.op, 'w', encoding='utf-8') as f:
        json.dump(final_index, f, ensure_ascii=False, indent=4)