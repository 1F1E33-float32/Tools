import argparse
import json
import os
import shutil

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audio_ext", default=".hca")
    p.add_argument("--audio_dir", default=r"/mnt/d/Fuck_VN/voice")
    p.add_argument("--index_json", default=r"/mnt/d/Fuck_VN/index.json")
    p.add_argument("--out_dir", default=r"/mnt/d/Fuck_VN/Umamusume")
    return p.parse_args(args=args, namespace=namespace)


def resolve_voice_key(name_lower: str, audio_map: dict) -> str | None:
    if name_lower in audio_map:
        return name_lower
    alt = f"{name_lower}_#1"
    if alt in audio_map:
        return alt
    return None


def main(audio_ext, audio_dir, index_path, out_dir):
    # 1. 收集所有 .hca文件，键为小写文件名（不含扩展名）
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
            v_lower = os.path.splitext(v)[0].lower()  # 只取不带扩展名的部分
            matched_key = resolve_voice_key(v_lower, audio_map)
            if matched_key:
                # 命中的话，统一记录为匹配到的（可能带 _#1）的文件名 + 扩展名
                rec_copy = rec.copy()
                rec_copy["Voice"] = matched_key + audio_ext.lower()
                if matched_key != v_lower:
                    print(f"未找到原音频，已使用带后缀的文件: {v} -> {rec_copy['Voice']}")
                new_data.append(rec_copy)
            else:
                print(f"找不到音频: Voice={v}")

    # 4. 把音频拷贝到 out_dir/{Speaker}/{Voice}
    for rec in tqdm(new_data):
        v = rec["Voice"]
        sp = rec["Speaker"]
        if v:
            dst_dir = os.path.join(out_dir, sp)
            os.makedirs(dst_dir, exist_ok=True)
            name_no_ext = os.path.splitext(v)[0].lower()
            src = audio_map.get(name_no_ext)
            if src:
                dst = os.path.join(dst_dir, v)
                shutil.move(src, dst)
            else:
                print(f"警告，源文件未找到（应当已在前面匹配）: {name_no_ext}")

    # 5. 写新的 index.json
    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, "index.json")
    with open(index_out, "w", encoding="utf-8") as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)
