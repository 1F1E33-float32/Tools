import argparse
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import av
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn

AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".opus")


def process_audio_file(file_path):
    try:
        with av.open(file_path, metadata_errors="ignore") as container:
            # container.duration 以微秒计；有些文件可能为 None
            duration_us = container.duration
            if duration_us is None:
                return 0.0
            return duration_us / 1_000_000
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0.0


def format_hms(seconds: float) -> str:
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def main(in_dir, num_threads):
    # 收集文件列表，并记录其所属的一级子文件夹名
    files = []
    file_to_subfolder = {}

    # 只统计 in_dir 下的一级子目录；如果存在直接位于 in_dir 根下的音频文件，将被忽略
    for entry in os.scandir(in_dir):
        if entry.is_dir():
            subfolder_name = entry.name
            for root, _, filenames in os.walk(entry.path):
                for fn in filenames:
                    if fn.lower().endswith(AUDIO_EXTENSIONS):
                        full_path = os.path.join(root, fn)
                        files.append(full_path)
                        file_to_subfolder[full_path] = subfolder_name

    if not files:
        print("未在指定目录的各子文件夹中找到音频文件。")
        return

    # 统计总数与每子文件夹时长
    total_duration = 0.0
    subfolder_durations = defaultdict(float)

    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>3.2f}%", "•", MofNCompleteColumn(), "•", TimeElapsedColumn(), "|", TimeRemainingColumn()) as progress:
        total_task = progress.add_task("Total", total=len(files))
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(process_audio_file, f): f for f in files}
            for future in as_completed(futures):
                file_path = futures[future]
                duration = future.result()
                total_duration += duration
                subfolder = file_to_subfolder[file_path]
                subfolder_durations[subfolder] += duration
                progress.update(total_task, advance=1)

    # 打印每个子文件夹的总时长
    print("\n各子文件夹总时长：")
    # 排序：按子文件夹名
    for subfolder in sorted(subfolder_durations.keys()):
        d = subfolder_durations[subfolder]
        print(f"{subfolder}: {d:.2f} s  {d / 60:.2f} m  ({format_hms(d)})")

    # 也打印总体（可选）
    print("\n总体：")
    print(f"{total_duration:.2f} s  {total_duration / 60:.2f} m  ({format_hms(total_duration)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", type=str, default=r"E:\Game_Dataset\WutheringWaves\OK")
    parser.add_argument("--num_threads", type=int, default=20)
    args = parser.parse_args()
    main(args.in_dir, args.num_threads)
