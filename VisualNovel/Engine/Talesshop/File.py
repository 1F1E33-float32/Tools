import os
import json
import shutil
import argparse
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument('--audio_ext',  default='.wav')
    p.add_argument('--audio_dir',  default=r"D:\Fuck_galgame\voice")
    p.add_argument('--index_json', default=r"D:\Fuck_galgame\index.json")
    p.add_argument('--out_dir',    default=r"D:\Dataset_VN_NoScene\Talesshop_Random Chatting-ui Geunyeo")
    return p.parse_args(args=args, namespace=namespace)

def main(audio_ext, audio_dir, index_path, out_dir):
    # 1. 收集所有音频文件，key = "foldername_filename"（小写，无扩展名） -> 音频完整路径
    audio_index = {}
    for root, _, files in os.walk(audio_dir):
        folder = os.path.basename(root)
        for f in files:
            if f.lower().endswith(audio_ext.lower()):
                name_no_ext = os.path.splitext(f)[0]
                key = f"{folder}_{name_no_ext}".lower()
                audio_index[key] = os.path.join(root, f)

    # 2. 读取旧的 index.json
    with open(index_path, encoding='utf-8') as fp:
        data = json.load(fp)

    # 3. 过滤并保证 Voice 带扩展名
    new_data = []
    for rec in data:
        v = rec.get('Voice')
        if not v:
            # 没有 Voice，直接保留
            new_data.append(rec)
            continue

        # 取 key（去扩展、小写）
        key = os.path.splitext(v)[0].lower()
        if key in audio_index:
            # 确保扩展名正确
            rec_copy = rec.copy()
            rec_copy['Voice'] = key + audio_ext.lower()
            new_data.append(rec_copy)
        else:
            print(f"跳过，找不到音频: Voice={v}")

    # 4. 按 Speaker 目录移动文件，文件名带扩展名
    for rec in tqdm(new_data, desc="移动音频文件"):
        filename = rec.get('Voice')
        if not filename:
            continue

        key = os.path.splitext(filename)[0]
        src = audio_index.get(key)
        if not src:
            print(f"警告，源文件未找到: {key}")
            continue

        speaker = rec.get('Speaker') or ''
        dst_dir = os.path.join(out_dir, speaker)
        os.makedirs(dst_dir, exist_ok=True)

        dst = os.path.join(dst_dir, filename)
        shutil.move(src, dst)

    # 5. 写新的 index.json 到 out_dir，Voice 都带上了 .wav
    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, 'index.json')
    with open(index_out, 'w', encoding='utf-8') as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(
        args.audio_ext,
        args.audio_dir,
        args.index_json,
        args.out_dir
    )