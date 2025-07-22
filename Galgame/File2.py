import os
import json
import argparse
from tqdm import tqdm
import av

def get_audio_duration(path: str) -> float:
    container = av.open(path, metadata_errors="ignore")
    # container.duration 单位是 AV_TIME_BASE（1e6）倍数
    if container.duration is not None:
        return container.duration / 1_000_000
    # fallback：遍历帧
    max_t = 0.0
    for frame in container.decode(audio=0):
        # frame.time 类型为 float（秒）
        if frame.time and frame.time > max_t:
            max_t = frame.time
    return max_t

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default=r"D:\Dataset_VN_NoScene\#OK ENG\TWD")
    parser.add_argument("--input-json", default="index.json")
    parser.add_argument("--output-json", default="index_with_duration.json")
    args = parser.parse_args()

    base_dir = args.folder
    in_path = os.path.join(base_dir, args.input_json)
    out_path = os.path.join(base_dir, args.output_json)

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_duration = 0.0
    valid_count = 0
    error_count = 0

    for entry in tqdm(data, ncols=150):
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

    # 显示统计信息
    print(f"已完成，带 duration 的新 JSON 保存在：{out_path}")
    print(f"统计信息：")
    print(f"  总条目数: {len(data)}")
    print(f"  成功处理: {valid_count}")
    print(f"  处理失败: {error_count}")
    print(f"  总时长: {total_duration:.3f} 秒 ({total_duration/60:.2f} 分钟)")

if __name__ == "__main__":
    main()