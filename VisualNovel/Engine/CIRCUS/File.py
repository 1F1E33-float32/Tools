import os
import json
import shutil

audio_root = r"D:\Fuck_VN"
output_root = r"E:\VN_Dataset\TMP_DATA\CIRCUS_Princess Party"

os.makedirs(output_root, exist_ok=True)
with open(r"D:\Fuck_VN\index.json", "r", encoding="utf-8") as f:
    index_data = json.load(f)

audio_cache = {}
for root, dirs, files in os.walk(audio_root):
    for file in files:
        rel_path = os.path.relpath(os.path.join(root, file), audio_root)
        audio_cache[rel_path.lower()] = os.path.join(root, file)

processed_data = []

for entry in index_data:
    speaker = entry["Speaker"]
    voice_path = entry["Voice"]

    normalized_path = voice_path.replace("/", os.sep).replace("\\", os.sep).lower()

    _, ext = os.path.splitext(normalized_path)
    candidates = [normalized_path] if ext else [normalized_path + ".wav", normalized_path + ".ogg"]

    src_path = None
    hit_key = None
    for key in candidates:
        if key in audio_cache:
            src_path = audio_cache[key]
            hit_key = key
            break

    if src_path:
        speaker_dir = os.path.join(output_root, speaker)
        os.makedirs(speaker_dir, exist_ok=True)

        filename = os.path.basename(src_path)
        dest_path = os.path.join(speaker_dir, filename)
        shutil.move(src_path, dest_path)

        entry["Voice"] = f"{filename}"
        processed_data.append(entry)
    else:
        print(f"找不到文件: {voice_path}，已尝试: {', '.join(candidates)}")

output_index = os.path.join(output_root, "index.json")
with open(output_index, "w", encoding="utf-8") as f:
    json.dump(processed_data, f, ensure_ascii=False, indent=2)
