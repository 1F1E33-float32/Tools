import re
import os
import json
import struct
import sqlite3
import argparse
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-fl", type=str, default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki\ConfigDB\db_flowState.db")
    parser.add_argument("-la", type=str, default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki\ConfigDB\ko\lang_multi_text.db")
    parser.add_argument("-fa", type=str, default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki\ConfigDB\db_favor.db")

    parser.add_argument("-au", type=str, default=r"D:\Wuthering Waves\Resource_ko")
    parser.add_argument("-op", type=str, default=r"D:\AI\Audio_Tools\python\WutheringWaves_KO_index.json")

    parser.add_argument("-md", type=str, default="KO") # CHS, CHT, EN, JA, KO
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    global mode
    if mode == "CHS" or mode == "CHT" or mode =="JA":
        text = text.replace('{PlayerName}', '漂泊者')
    elif mode == "EN":
        text = text.replace('{PlayerName}', 'Rover')
    elif mode == "KO":
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
    if mode == "CHS" or mode == "CHT" or mode =="JA":
        if id == 1501 or id == 1604:
            return "漂泊者_男"
        elif id == 1502 or id == 1605:
            return "漂泊者_女"
        elif id == 83 or id == 354:
            return ["漂泊者_男", "漂泊者_女"]
        
    elif mode == "EN":
        if id == 1501 or id == 1604:
            return "Rover_male"
        elif id == 1502 or id == 1605:
            return "Rover_female"
        elif id == 83 or id == 354:
            return ["Rover_male", "Rover_female"]
        
    elif mode == "KO":
        if id == 1501 or id == 1604:
            return "방랑자_남성"
        elif id == 1502 or id == 1605:
            return "방랑자_여성"
        elif id == 83 or id == 354:
            return ["방랑자_남성", "방랑자_여성"]
        
def clean_bin_data(data):
    start_index = data.find(b'[{')
    end_index = data.rfind(b'}]')
    if start_index != -1 and end_index != -1:
        cleaned_data = data[start_index:end_index+2]
        return cleaned_data
    return None

def extract_talk_items(data):
    result = []
    for dictionary_A in data:
        if dictionary_A.get("Name") == "ShowTalk":
            talk_items = dictionary_A.get("Params", {}).get("TalkItems", [])
            for dictionary_B in talk_items:
                #if dictionary_B.get("Type") == "Talk" or dictionary_B.get("PlayVoice"):
                result.append({"TidTalk": dictionary_B.get("TidTalk"), "WhoId": dictionary_B.get("WhoId")})
    return result

def get_speaker(cursor_lang, who_id):
    cursor_lang.execute("SELECT Content FROM MultiText WHERE Id=?", (f"Speaker_{who_id}_Name",))
    result = cursor_lang.fetchone()
    if result:
        return result[0]

def get_text(cursor_lang, tid_talk):
    cursor_lang.execute("SELECT Content FROM MultiText WHERE Id=?", (tid_talk,))
    result = cursor_lang.fetchone()
    if result:
        return result[0]

def process_flowstate(cursor_flowstate, cursor_lang):
    cursor_flowstate.execute("SELECT binData FROM flowstate")
    bin_datas = cursor_flowstate.fetchall()

    result = []

    for bin_data in tqdm(bin_datas):
        bin_data = bin_data[0]
        cleaned_data = clean_bin_data(bin_data)
        if cleaned_data is None:
            continue
        try:
            cleaned_data_str = cleaned_data.decode('utf-8')
            json_data = json.loads(cleaned_data_str)
            extracted_items = extract_talk_items(json_data)
            for item in extracted_items:
                tid_talk = item["TidTalk"]
                talk_text = get_text(cursor_lang, tid_talk)
                if not talk_text or not tid_talk:
                    continue
                
                talk_text = text_cleaning(talk_text)

                who_id = item["WhoId"]
                if who_id == 83 or who_id == 354:
                    result.append({"WhoId": name_mappping(who_id)[0], "Text": talk_text, "TidTalk": tid_talk + "_M"})
                    result.append({"WhoId": name_mappping(who_id)[1], "Text": talk_text, "TidTalk": tid_talk + "_F"})
                else:
                    speaker_name = get_speaker(cursor_lang, who_id)
                    speaker_name = speaker_name if speaker_name else "None"
                    speaker_name = speaker_name.replace('"', '').replace(':', '')
                    sex_pattern = r"\{Male=(.*?);Female=(.*?)\}"
                    match_sex = re.search(sex_pattern, talk_text)
                    if match_sex:
                        male_value = match_sex.group(1)
                        female_value = match_sex.group(2)
                        result_with_male = re.sub(sex_pattern, male_value, talk_text)
                        result_with_female = re.sub(sex_pattern, female_value, talk_text)
                        result.append({"WhoId": speaker_name, "Text": result_with_male, "TidTalk": tid_talk + "_M"})
                        result.append({"WhoId": speaker_name, "Text": result_with_female, "TidTalk": tid_talk + "_F"})
                        continue
                    result.append({"WhoId": speaker_name, "Text": talk_text, "TidTalk": tid_talk})

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Error: {e}")
            continue

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

    function_name = re.compile(rb'/Game/Aki/WwiseAudio/[\w/]+/[\w\.]+')
    function_favorword = re.compile(rb'FavorWord_\d+_Content')

    result = []
    for row in rows:
        bin_data = row[0]
        match_function_name = function_name.findall(bin_data)[0]
        match_function_favorword = function_favorword.findall(bin_data)[0]

        try:
            decoded_name = match_function_name.decode('utf-8', errors='ignore')
            decoded_name = decoded_name.split(".")[-1]
        except UnicodeDecodeError:
            decoded_name = None
        
        try:
            decoded_favorword = match_function_favorword.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            decoded_favorword = None

        result.append({"function_names": decoded_name, "function_favorwords": decoded_favorword})
    return result

def process_favorword(cursor_favorword, cursor_lang, au):
    results = []

    favorwords = get_favorword(cursor_favorword)
    for favorword in tqdm(favorwords):
        function_name = favorword["function_names"] + ".bnk"
        function_favorword = favorword["function_favorwords"]
        role_id = function_favorword.split("_")[1][:4]
        if role_id in ["1501", "1502", "1604", "1605"]:
            Whoid = name_mappping(role_id)
        else:
            role_id_sql = f"RoleInfo_{role_id}_Name"
            cursor_lang.execute("SELECT Content FROM MultiText WHERE Id=?", (role_id_sql,))
            Whoid = cursor_lang.fetchone()[0]

        wwise_short_name = get_bnk(find_file(function_name, au))
        if len(wwise_short_name) != 1:
            print(f"{function_name}, {wwise_short_name}")
        wwise_short_name = wwise_short_name[0]["SourceID"]

        cursor_lang.execute("SELECT Content FROM MultiText WHERE Id=?", (function_favorword,))
        text = cursor_lang.fetchone()[0]
        if text =='（语气词）':
            continue
        text = text_cleaning(text)

        results.append({"WhoId": Whoid, "Text": text, "TidTalk": wwise_short_name})

    return results

if __name__ == "__main__":
    global mode
    args = parse_args()
    mode = args.md

    conn_flowstate = sqlite3.connect(args.fl)
    cursor_flowstate = conn_flowstate.cursor()

    conn_lang = sqlite3.connect(args.la)
    cursor_lang = conn_lang.cursor()

    conn_favorword = sqlite3.connect(args.fa)
    cursor_favorword = conn_favorword.cursor()

    extracted_flowstate = process_flowstate(cursor_flowstate, cursor_lang)
    extracted_favorword = process_favorword(cursor_favorword, cursor_lang, args.au)

    conn_flowstate.close()
    conn_lang.close()
    conn_favorword.close()

    final_index = extracted_favorword + extracted_flowstate

    with open(args.op, 'w', encoding='utf-8') as f:
        json.dump(final_index, f, ensure_ascii=False, indent=4)