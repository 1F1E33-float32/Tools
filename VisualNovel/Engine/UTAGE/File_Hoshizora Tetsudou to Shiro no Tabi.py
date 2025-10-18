import argparse
import json
import os
import shutil

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audio_dir", default=r"D:\Fuck_VN\voice")
    p.add_argument("--index_json", default=r"D:\Fuck_VN\index.json")
    p.add_argument("--out_dir", default=r"E:\VN_Dataset\TMP_DATA\Shiratamaco_Hoshizora Tetsudou to Shiro no Tabi")
    return p.parse_args(args=args, namespace=namespace)


def main(audio_dir, index_path, out_dir):
    with open(index_path, encoding="utf-8") as fp:
        data = json.load(fp)

    new_data = []
    for rec in tqdm(data, desc="Processing", ncols=150):
        v = rec.get("Voice")
        if v is None:
            new_data.append(rec)
            continue

        voice_path = v.replace('/', os.sep).replace('\\', os.sep)
        src = os.path.join(audio_dir, voice_path)

        if os.path.isfile(src):
            rec_copy = rec.copy()
            rec_copy["Voice"] = os.path.basename(voice_path)
            new_data.append(rec_copy)

            sp = rec.get("Speaker") or ""
            dst_dir = os.path.join(out_dir, sp)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, os.path.basename(voice_path))
            shutil.move(src, dst)
        else:
            print(f"跳过，找不到音频: {src}")

    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, "index.json")
    with open(index_out, "w", encoding="utf-8") as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)

    print(f"Total processed: {len(new_data)}")


if __name__ == "__main__":
    args = parse_args()
    main(args.audio_dir, args.index_json, args.out_dir)
