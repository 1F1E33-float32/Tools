import os
import av
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn

AUDIO_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".opus")

def process_audio_file(file_path):
    try:
        container = av.open(file_path, metadata_errors="ignore")
        duration = container.duration / 1_000_000  # Convert microseconds to seconds
        return duration
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0  # Return 0 duration if there's an error

def main(in_dir, num_processes):
    audio_files = []
    total_duration = 0

    # Collect all audio files in in_dir
    for root, _, files in os.walk(in_dir):
        for file in files:
            if file.lower().endswith(AUDIO_EXTENSIONS):
                full_path = os.path.join(root, file)
                audio_files.append(full_path)
    
    if not audio_files:
        print("未在指定目录中找到音频文件。")
        return
    
    with Progress(TextColumn("[progress.description]{task.description}"), BarColumn(), "[progress.percentage]{task.percentage:>3.1f}%", "•", MofNCompleteColumn(), "•", TimeElapsedColumn(), "|", TimeRemainingColumn()) as progress:
        total_task = progress.add_task("Total", total=len(audio_files))

        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            futures = {executor.submit(process_audio_file, file): file for file in audio_files}
            for future in as_completed(futures):
                duration = future.result()
                total_duration += duration
                progress.update(total_task, advance=1)

    # Print the total duration in seconds
    print(f"Total duration of all audio files: {total_duration:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", type=str, default=r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\EXP\v")
    parser.add_argument("--num_processes", type=int, default=20)
    args = parser.parse_args()
    main(args.in_dir, args.num_processes)