import json
import os
import re

datacfg_3 = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\datacfg_3.json"
datacfg_4 = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\datacfg_4.json"
datacfg_5 = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\datacfg_5.json"


def load_entries(path, *keys):
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    entries = []
    for key in keys:
        entries.extend(cfg.get(key, [None, []])[1])
    return entries


en3 = load_entries(datacfg_3, "json_story_role_audio", "json_story_audio_branch")
en4 = load_entries(datacfg_4, "json_story_audio_main", "json_role_audio", "json_fight_audio", "json_story_audio", "json_ui_audio")
en5 = load_entries(datacfg_5, "json_story_audio_role", "json_story_audio_system", "json_story_audio_short")

all_entries = en3 + en4 + en5
audio_map = {}
for entry in all_entries:
    _id = entry[0]
    a1 = entry[1]
    a2 = entry[2]
    if _id not in audio_map:
        audio_map[_id] = (a1, a2)

print(f"Loaded {len(audio_map)} unique audio entries")

folder_path = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\Story\ZResourcesLib\configs\story\steps"


def fnv1_32(text):
    FNV_PRIME = 0x01000193
    OFFSET_BIAS = 0x811C9DC5

    h = OFFSET_BIAS
    for b in text.encode("utf-8"):
        h = (h * FNV_PRIME) & 0xFFFFFFFF
        h ^= b
    return h


def speaker_cleaning(text):
    text = text.replace("?", "？").replace('"', "").replace(" ", "")
    text = text.replace("!+*?%&#", "□□□").replace("!+*？%&#", "□□□")
    return text


def text_cleaning(text):
    text = re.sub(r"<[^>]*>", "", text)
    text = text.replace("\n", "").replace("　", "")
    text = text.replace("!+*?%&#", "□□□").replace("!+*？%&#", "□□□")
    return text


results = []
seen = set()

for filename in os.listdir(folder_path):
    if not filename.lower().endswith(".json"):
        continue

    file_path = os.path.join(folder_path, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data[2]:
        speaker_raw = item[2][11]
        voice_raw = item[2][14]
        text_raw = item[2][15]

        if not (speaker_raw and voice_raw and text_raw):
            continue
        if len(speaker_raw) < 5 or len(text_raw) < 5:
            continue

        voice_key = voice_raw.replace(" ", "")
        voice_key = voice_key.split("#")[0]
        voice_key = voice_key.split("&")[0]
        voice_key = int(voice_key)
        if voice_key not in audio_map:
            continue

        idx1, idx2 = audio_map[voice_key]
        voice_hash = fnv1_32(idx1)

        zh_s, en_s, kr_s, jp_s = speaker_raw[0], speaker_raw[2], speaker_raw[3], speaker_raw[4]
        zh_t, en_t, kr_t, jp_t = text_raw[0], text_raw[2], text_raw[3], text_raw[4]
        if any(val == "" for val in (zh_s, en_s, kr_s, jp_s)) or any(val == "" for val in (zh_t, en_t, kr_t, jp_t)):
            continue

        speaker = {
            "zh": speaker_cleaning(zh_s),
            "en": speaker_cleaning(en_s),
            "kr": speaker_cleaning(kr_s),
            "jp": speaker_cleaning(jp_s),
        }
        text = {
            "zh": text_cleaning(zh_t),
            "en": text_cleaning(en_t),
            "kr": text_cleaning(kr_t),
            "jp": text_cleaning(jp_t),
        }

        if voice_hash in seen:
            continue
        seen.add(voice_hash)
        results.append({"Speaker": speaker, "Voice": voice_hash, "Text": text, "Directory": idx2})

output_path = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\index.json"
with open(output_path, "w", encoding="utf-8") as f_out:
    json.dump(results, f_out, ensure_ascii=False, indent=4)

print(f"Processed {len(results)} entries. Output saved to {output_path}.")
