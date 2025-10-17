import argparse
import json
import os
import shutil

from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeRemainingColumn


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audio_ext", default=".ogg")
    p.add_argument("--audio_dir", default=r"D:\Fuck_VN\voice")
    p.add_argument("--index_json", default=r"D:\Fuck_VN\index.json")
    p.add_argument("--out_dir", default=r"E:\VN_Dataset\TMP_DATA\CLOCKUP team.DYO_Zwei Worter - HD Remaster")
    return p.parse_args(args=args, namespace=namespace)


def build_file_index(directory):
    index = {}
    for root, dirs, files in os.walk(directory):
        for filename in files:
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            index[filename.lower()] = rel_path
    return index


def main(audio_ext, audio_dir, index_path, out_dir):
    with open(index_path, encoding="utf-8") as fp:
        data = json.load(fp)

    os.makedirs(out_dir, exist_ok=True)
    new_data = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TaskProgressColumn(), TimeRemainingColumn()) as progress:
        file_index = build_file_index(audio_dir)
        task = progress.add_task("Processing", total=len(data))

        for rec in data:
            v = rec["Voice"]
            sp = rec["Speaker"]

            # 从索引中查找
            target_filename = v + audio_ext
            rel_path = file_index.get(target_filename.lower())

            if rel_path:
                src = os.path.join(audio_dir, rel_path)
                # 目标路径：out_dir/Speaker/Voice
                dst_dir = os.path.join(out_dir, sp)
                os.makedirs(dst_dir, exist_ok=True)
                # 使用index中的文件名（保持一致性）
                voice_filename = v + audio_ext
                dst = os.path.join(dst_dir, voice_filename)
                shutil.move(src, dst)

                # 更新记录中的Voice字段
                rec_copy = rec.copy()
                rec_copy["Voice"] = voice_filename
                new_data.append(rec_copy)
            else:
                print(f"找不到文件: {target_filename}")

            progress.update(task, advance=1)

    index_out = os.path.join(out_dir, "index.json")
    with open(index_out, "w", encoding="utf-8") as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)
