import argparse
import json
import os
import shutil

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audio_ext", default=".ogg")
    p.add_argument("--audio_dir", default=r"D:\Fuck_VN\voice")
    p.add_argument("--index_json", default=r"D:\Fuck_VN\index.json")
    p.add_argument("--out_dir", default=r"E:\VN_Dataset\TMP_DATA\Yuzusoft_Senren Banka")
    return p.parse_args(args=args, namespace=namespace)


def main(audio_ext, audio_dir, index_path, out_dir):
    # 1. 收集所有 .ogg 文件，键为小写文件名（不含扩展名）
    audio_map = {}
    for root, _, files in os.walk(audio_dir):
        for f in files:
            if f.lower().endswith(audio_ext.lower()):
                name_lower = os.path.splitext(f)[0].lower()
                audio_map[name_lower] = os.path.join(root, f)

    # 2. 读取 index.json
    with open(index_path, encoding="utf-8") as fp:
        data = json.load(fp)

    # 3. 过滤：Voice 为 None 或者 找得到对应音频的保留
    new_data = []
    for rec in data:
        v = rec.get("Voice")
        if v is None:
            new_data.append(rec)
        else:
            v_lower = v.lower()
            if v_lower in audio_map:
                # 记录一致使用小写文件名
                rec_copy = rec.copy()
                rec_copy["Voice"] = v_lower + audio_ext.lower()
                new_data.append(rec_copy)
            else:
                print(f"跳过，找不到音频: Voice={v}")

    # 4. 把音频拷贝到 out_dir/{Speaker}/{Voice}
    for rec in tqdm(new_data):
        v = rec.get("Voice")
        sp = rec.get("Speaker") or ""
        if v:
            dst_dir = os.path.join(out_dir, sp)
            os.makedirs(dst_dir, exist_ok=True)
            name_no_ext = os.path.splitext(v)[0]
            src = audio_map.get(name_no_ext)
            if src:
                dst = os.path.join(dst_dir, v)
                shutil.move(src, dst)
            else:
                print(f"警告，源文件未找到: {name_no_ext}")

    # 5. 写新的 index.json
    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, "index.json")
    with open(index_out, "w", encoding="utf-8") as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)
