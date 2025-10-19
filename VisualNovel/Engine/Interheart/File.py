import argparse
import json
import os
import shutil

import av
from tqdm import tqdm


def get_audio_duration(path: str) -> float:
    container = av.open(path, metadata_errors="ignore")
    if container.duration is not None:
        time = container.duration / 1_000_000
        container.close()
        return time


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audio_ext", default=".ogg")
    p.add_argument("--audio_dir", default=r"D:\Fuck_VN\voice")
    p.add_argument("--index_json", default=r"D:\Fuck_VN\index.json")
    p.add_argument("--out_dir", default=r"E:\VN_Dataset\TMP_DATA\Shibasoft_Mama x Kano ~Oshiego no Okaa-san ga Ecchi na Sensei de, Musume no Sewa o Yaitara Dame Desu ka~")
    return p.parse_args(args=args, namespace=namespace)


def main(audio_ext, audio_dir, index_path, out_dir):
    audio_map = {}
    for root, _, files in os.walk(audio_dir):
        for f in files:
            if f.lower().endswith(audio_ext.lower()):
                name_lower = os.path.splitext(f)[0].lower()
                audio_map[name_lower] = os.path.join(root, f)

    with open(index_path, encoding="utf-8") as fp:
        data = json.load(fp)

    new_data = []
    for rec in data:
        v = rec.get("Voice")
        if v is None:
            new_data.append(rec)
        else:
            v_lower = v.lower()
            if v_lower in audio_map:
                rec_copy = rec.copy()
                rec_copy["Voice"] = v_lower + audio_ext.lower()
                new_data.append(rec_copy)
            else:
                print(f"跳过，找不到音频: Voice={v}")

    final_data = []
    for rec in tqdm(new_data, ncols=150):
        v = rec.get("Voice")
        sp = rec.get("Speaker")
        src = os.path.join(audio_dir, rec["Folder"], rec["Voice"])
        try:
            duration = get_audio_duration(src)
        except Exception as e:
            print(f"跳过，无法获取时长: Voice={rec['Voice']}, 错误: {e}")
            continue
        if duration > 0:
            dst_dir = os.path.join(out_dir, sp)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, rec["Voice"])
            shutil.move(src, dst)
            final_data.append(rec)
        else:
            print(f"跳过，时长异常 (duration={duration}s): Voice={rec['Voice']}")

    new_data = final_data

    for rec in new_data:
        rec.pop("Folder", None)

    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, "index.json")
    with open(index_out, "w", encoding="utf-8") as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)
