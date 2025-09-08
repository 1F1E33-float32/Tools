import os
import json
import argparse
from tqdm import tqdm
import av

def get_audio_duration(path):
    container = av.open(path, metadata_errors="ignore")
    if container.duration is not None:
        return container.duration / 1_000_000
    max_t = 0.0
    for frame in container.decode(audio=0):
        if frame.time and frame.time > max_t:
            max_t = frame.time
    return max_t

def process_one_folder(base_dir, input_json, output_json):
    in_path = os.path.join(base_dir, input_json)
    out_path = os.path.join(base_dir, output_json)

    if not os.path.isfile(in_path):
        print(f"[WARN] 子目录缺少 {input_json}: {in_path}")
        return

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_duration = 0.0
    valid_count = 0
    error_count = 0

    for entry in tqdm(data, ncols=150, desc=os.path.basename(base_dir) or base_dir):
        speaker = entry.get("Speaker")
        voice   = entry.get("Voice")

        if speaker and voice:
            audio_file = os.path.join(base_dir, speaker, voice)
            try:
                duration = get_audio_duration(audio_file)
                if duration > 0:
                    total_duration += duration
                    valid_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"[WARN] 无法读取音频 {audio_file}: {e}")
                duration = -1.0
                error_count += 1
        else:
            duration = -1.0

        entry["duration"] = round(duration, 3)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"[{base_dir}] 总条目数: {len(data)}")
    print(f"[{base_dir}] 成功处理: {valid_count}")
    print(f"[{base_dir}] 处理失败: {error_count}")
    print(f"[{base_dir}] 总时长:   {total_duration/60:.2f} 分钟")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default=r"D:\Dataset_VN_NoScene\#OK_20250828")
    parser.add_argument("--input-json", default="index.json")
    parser.add_argument("--output-json", default="index_with_duration.json")
    args = parser.parse_args()

    parent_dir = args.folder

    # 只扫描一层子文件夹
    for entry in os.scandir(parent_dir):
        if entry.is_dir():
            process_one_folder(entry.path, args.input_json, args.output_json)