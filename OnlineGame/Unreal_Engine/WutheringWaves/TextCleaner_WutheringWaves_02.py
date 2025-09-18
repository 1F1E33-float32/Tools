import argparse
import inspect
import json
import os
import random
import re
import sqlite3
import struct

from Aki.FavorWord import FavorWord
from Aki.FlowState import FlowState
from tqdm import tqdm

LANGS = ["zh", "ja", "en", "ko"]
LANG_DIR_MAP = {
    "zh": "zh-Hans",
    "ja": "ja",
    "en": "en",
    "ko": "ko",
}

ROVER_NAME = {
    "zh": ("漂泊者_男", "漂泊者_女"),
    "ja": ("漂泊者_男", "漂泊者_女"),
    "en": ("Rover_male", "Rover_female"),
    "ko": ("방랑자_남성", "방랑자_여성"),
}


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\Client\Content\Aki")
    parser.add_argument("--out_dir", type=str, default=r"E:\Game_Dataset\WutheringWaves\EXP")
    return parser.parse_args(args=args, namespace=namespace)


_PAIR_PAT = re.compile(r"\{Male\s*=\s*([^;]+?)\s*;Female\s*=\s*([^}]+?)\s*\}")


def text_cleaning(text, sex, lang):
    if sex == "M":
        text = _PAIR_PAT.sub(r"\1", text)
        if lang == "zh":
            text = text.replace(r"{TA}", "他")
    elif sex == "F":
        text = _PAIR_PAT.sub(r"\2", text)
        if lang == "zh":
            text = text.replace(r"{TA}", "她")
    elif sex is None:
        if lang == "zh":
            text = text.replace(r"{TA}", random.choice(("他", "她")))

    text = text.replace("（", "").replace("）", "").replace("(", "").replace(")", "").replace("「", "").replace("」", "").replace('"', "").replace("\r", "").replace("\n", "")
    text = re.sub(r"<color=[^>]+>(.*?)<\/color>", r"\1", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("<", "")
    return text


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
        if name.startswith("_") or name.endswith("Length") or name in seen:
            continue
        try:
            if inspect.signature(fn).parameters:
                continue
        except (ValueError, TypeError):
            continue

        length_fn = getattr(obj, name + "Length", None)
        if callable(length_fn):
            arr = []
            for i in range(length_fn()):
                arr.append(_convert_value(fn(i)))
            result[name] = arr
            continue

        result[name] = _convert_value(fn())

    return result


def load_multitext_db(db_path, lang, out_dict):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT Id, Content FROM MultiText")
    for _id, content in cur.fetchall():
        if r"{PlayerName}" in content:
            continue
        out_dict[f"{lang}_{_id}"] = content
    conn.close()


_AUDIO_RE = re.compile(r"^(?P<lang>zh|ja|en|ko)_vo_(?P<idx>[^.]+)\.opus$", re.I)


def build_flow_audio_map(root):
    ex_base = os.path.join(root, "WwiseAudio_Generated", "WwiseExternalSource")

    mapping = {}
    for fname in tqdm(os.listdir(ex_base), ncols=150, desc="flow_audio_map"):
        m = _AUDIO_RE.match(fname)
        if not m:
            continue
        lang = m.group("lang").lower()
        idx = m.group("idx")
        key = f"{lang}_{idx}"
        mapping[key] = os.path.join(ex_base, fname)
    return mapping


def build_favor_audio_map(root):
    def get_bnk(file_path):
        with open(file_path, "rb") as f:
            f.seek(56)
            num_blocks = struct.unpack("<I", f.read(4))[0]
            ids = []
            for _ in range(num_blocks):
                chunk_type = struct.unpack("B", f.read(1))[0]
                chunk_size = struct.unpack("<I", f.read(4))[0]
                data = f.read(chunk_size)
                if chunk_type == 0x02 and chunk_size >= 9:
                    source_id = struct.unpack("<I", data[9:13])[0]
                    ids.append(source_id)
            return ids

    event_base = os.path.join(root, "WwiseAudio_Generated", "Event")
    media_base = os.path.join(root, "WwiseAudio_Generated", "Media")

    result = {}
    for lang in ("zh", "ja", "en", "ko"):
        ev_lang_dir = os.path.join(event_base, lang)

        for fname in tqdm(os.listdir(ev_lang_dir), ncols=150, desc=f"{lang}_favor_audio_map"):
            bnk_path = os.path.join(ev_lang_dir, fname)
            ids = get_bnk(bnk_path)
            if len(ids) == 1:
                wem = os.path.join(media_base, lang, f"{ids[0]}.opus")
                if os.path.exists(wem):
                    key = os.path.splitext(fname)[0]
                    key = f"{lang}_{key}"
                    result[key] = wem

    return result


def process_flowstate(cursor_flowstate):
    cursor_flowstate.execute("SELECT binData FROM flowstate")
    bin_datas = cursor_flowstate.fetchall()

    result = []
    for bin_data in tqdm(bin_datas, ncols=150, desc="flowstate"):
        fw = FlowState.GetRootAsFlowState(bin_data[0], 0)
        data = fb_to_dict(fw)
        json_data = json.loads(data.get("Actions", "[]"))
        for node in json_data:
            if node.get("Name") == "ShowTalk":
                for item in node.get("Params", {}).get("TalkItems", []):
                    if item.get("WhoId") is None:
                        continue
                    result.append({"TidTalk": item["TidTalk"], "WhoId": item["WhoId"]})
    return result


def process_favorword(cursor_favorword):
    cursor_favorword.execute("SELECT BinData FROM favorword")
    rows = cursor_favorword.fetchall()

    res = []
    for row in tqdm(rows, ncols=150, desc="favorword"):
        fw = FavorWord.GetRootAsFavorWord(row[0], 0)
        data = fb_to_dict(fw)
        res.append({
            "RoleId": data["RoleId"],
            "Voice": data["Voice"].split(".")[-1],
            "Content": data["Content"],
        })
    return res


def find_file(file_name, start_dir):
    for root, _, files in os.walk(start_dir):
        if file_name in files:
            return os.path.join(root, file_name)
    return None


if __name__ == "__main__":
    args = parse_args()

    root = args.root
    out_dir = args.out_dir

    cfg_dir = os.path.join(root, "ConfigDB")
    flowstate_db = os.path.join(cfg_dir, "db_flowState.db")
    favor_db = os.path.join(cfg_dir, "db_favor.db")

    lang_multi_text = {}
    for lang in LANGS:
        path = os.path.join(cfg_dir, LANG_DIR_MAP[lang], "lang_multi_text.db")
        load_multitext_db(path, lang, lang_multi_text)

    flow_audio_map = build_flow_audio_map(root)
    favor_audio_map = build_favor_audio_map(root)

    conn_flow = sqlite3.connect(flowstate_db)
    cur_flow = conn_flow.cursor()
    conn_favor = sqlite3.connect(favor_db)
    cur_favor = conn_favor.cursor()

    extracted_flowstate = process_flowstate(cur_flow)
    extracted_favorwords = process_favorword(cur_favor)

    conn_flow.close()
    conn_favor.close()

    os.makedirs(out_dir, exist_ok=True)

    for lang in LANGS:
        result1 = []
        result2 = []
        # 剧情控制流解析
        for item in extracted_flowstate:
            # 不区分性别的音频
            voice_flowstate = flow_audio_map.get(f"{lang}_{item['TidTalk']}")
            text_flowstate = lang_multi_text.get(f"{lang}_{item['TidTalk']}")
            speaker_flowstate = lang_multi_text.get(f"{lang}_Speaker_{item['WhoId']}_Name")
            if voice_flowstate and text_flowstate and speaker_flowstate:
                text_flowstate = text_cleaning(text_flowstate, None, lang)
                speaker_flowstate = speaker_flowstate.replace("?", "？").replace(" ", "").replace('"', "").replace(":", " ")  # 沟槽的Windows的保留字符
                result1.append({"WhoId": item["WhoId"], "Speaker": speaker_flowstate, "Voice": voice_flowstate, "Text": text_flowstate})
                voice_flowstate = text_flowstate = speaker_flowstate = None
                continue

            # 女主或者与女主有关的音频
            voice_flowstate_f = flow_audio_map.get(f"{lang}_{item['TidTalk']}_F")
            text_flowstate_f = lang_multi_text.get(f"{lang}_{item['TidTalk']}")
            if item["WhoId"] == 83 or item["WhoId"] == 354:  # 直接查表会查到漂泊者这一个名字，实际上要分性别处理的，所以手动映射
                speaker_flowstate_f = ROVER_NAME.get(lang)[1]
            else:
                speaker_flowstate_f = lang_multi_text.get(f"{lang}_Speaker_{item['WhoId']}_Name")
            if voice_flowstate_f and text_flowstate_f and speaker_flowstate_f:
                text_flowstate_f = text_cleaning(text_flowstate_f, "F", lang)
                speaker_flowstate_f = speaker_flowstate_f.replace("?", "？").replace(" ", "").replace('"', "").replace(":", " ")  # 沟槽的Windows的保留字符
                result1.append({"WhoId": item["WhoId"], "Speaker": speaker_flowstate_f, "Voice": voice_flowstate_f, "Text": text_flowstate_f})
                voice_flowstate_f = text_flowstate_f = speaker_flowstate_f = None

            # 男主或者与男主有关的音频
            voice_flowstate_m = flow_audio_map.get(f"{lang}_{item['TidTalk']}_M")
            text_flowstate_m = lang_multi_text.get(f"{lang}_{item['TidTalk']}")
            if item["WhoId"] == 83 or item["WhoId"] == 354:
                speaker_flowstate_m = ROVER_NAME.get(lang)[0]
            else:
                speaker_flowstate_m = lang_multi_text.get(f"{lang}_Speaker_{item['WhoId']}_Name")
            if voice_flowstate_m and text_flowstate_m and speaker_flowstate_m:
                text_flowstate_m = text_cleaning(text_flowstate_m, "M", lang)
                speaker_flowstate_m = speaker_flowstate_m.replace("?", "？").replace(" ", "").replace('"', "").replace(":", " ")  # 沟槽的Windows的保留字符
                result1.append({"WhoId": item["WhoId"], "Speaker": speaker_flowstate_m, "Voice": voice_flowstate_m, "Text": text_flowstate_m})
                voice_flowstate_m = text_flowstate_m = speaker_flowstate_m = None

        out_path = os.path.join(out_dir, f"{lang}_flowstate.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result1, f, ensure_ascii=False, indent=4)

        # 角色档案解析
        for item in extracted_favorwords:
            voice_favorwords = favor_audio_map.get(f"{lang}_{item['Voice']}")
            text_favorwords = lang_multi_text.get(f"{lang}_{item['Content']}")
            speaker_favorwords = lang_multi_text.get(f"{lang}_RoleInfo_{item['RoleId']}_Name")
            if voice_favorwords and text_favorwords and speaker_favorwords:
                text_favorwords = text_cleaning(text_favorwords, None, None)
                if text_favorwords == "语气词" or text_favorwords == "台詞なし" or text_favorwords == "*Exhale*":
                    continue
                if item["RoleId"] in [1501, 1605, 1406]:  # 男主  衍射，湮灭，气动
                    speaker_favorwords = ROVER_NAME.get(lang)[0]
                if item["RoleId"] in [1502, 1604, 1408]:  # 女主  衍射，湮灭，气动
                    speaker_favorwords = ROVER_NAME.get(lang)[1]
                result2.append({"RoleId": item["RoleId"], "Speaker": speaker_favorwords, "Voice": voice_favorwords, "Text": text_favorwords})
                voice_favorwords = text_favorwords = speaker_favorwords = None

        out_path = os.path.join(out_dir, f"{lang}_favorwords.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result2, f, ensure_ascii=False, indent=4)
