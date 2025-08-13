import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
import av

AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".opus")

def process_audio_file(file_path):
    try:
        with av.open(file_path, metadata_errors="ignore") as container:
            duration = container.duration / 1_000_000
        return duration
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def main(in_dir, num_threads):
    audio_files = []
    total_duration = 0

    for root, _, files in os.walk(in_dir):
        for file in files:
            if file.lower().endswith(AUDIO_EXTENSIONS):
                full_path = os.path.join(root, file)
                audio_files.append(full_path)
    
    if not audio_files:
        print("未在指定目录中找到音频文件。")
        return
    
    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:>3.2f}%", "•", MofNCompleteColumn(), "•", TimeElapsedColumn(), "|", TimeRemainingColumn()) as progress:
        total_task = progress.add_task("Total", total=len(audio_files))
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(process_audio_file, file): file for file in audio_files}
            for future in as_completed(futures):
                duration = future.result()
                total_duration += duration
                progress.update(total_task, advance=1)

    print(f"{total_duration:.2f} s  {total_duration/60:.2f}m")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", type=str, default=r"D:\Dataset_VN_NoScene\##OnlineGame_Dataset\OnlineGame_Dataset\Reverse1999_KO")
    parser.add_argument("--num_threads", type=int, default=20)
    args = parser.parse_args()
    main(args.in_dir, args.num_threads)