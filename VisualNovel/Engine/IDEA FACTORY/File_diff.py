import argparse
import json
import os


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--audio_ext", default=".hca")
    p.add_argument("--audio_dir", default=r"D:\Fuck_VN\voice")
    p.add_argument("--index_json", default=r"D:\\Fuck_VN\\index.json")
    return p.parse_args(args=args, namespace=namespace)


def main(audio_ext: str, audio_dir: str, index_path: str) -> None:
    ext_lower = audio_ext.lower()

    # 1) scan voice folder for files with the given extension
    voice_files_set = set()
    for root, _, files in os.walk(audio_dir):
        for f in files:
            if f.lower().endswith(ext_lower):
                base = os.path.splitext(f)[0].lower()
                voice_files_set.add(base)

    # 2) load index.json and collect Voice values (compare by basename)
    with open(index_path, encoding="utf-8") as fp:
        data = json.load(fp)

    index_voice_set = set()
    for rec in data:
        v = rec.get("Voice")
        if not v:
            continue
        v_str = str(v).strip().lower()
        # if the index already includes extension, strip it for comparison
        if v_str.endswith(ext_lower):
            v_str = os.path.splitext(v_str)[0]
        index_voice_set.add(v_str)

    # 3) compute differences
    missing_in_folder = sorted(index_voice_set - voice_files_set)
    extra_in_folder = sorted(voice_files_set - index_voice_set)

    # 4) print results
    print(f"index.json 中 Voice 条目数: {len(index_voice_set)}")
    print(f"voice 文件夹中 *{ext_lower} 文件数: {len(voice_files_set)}")

    print(f"\n缺失于 voice 文件夹（index.json 有，文件夹无）: {len(missing_in_folder)}")
    for name in missing_in_folder:
        print(name)

    print(f"\n多余于 voice 文件夹（文件夹有，index.json 无）: {len(extra_in_folder)}")
    for name in extra_in_folder:
        print(name)
        
    print(len(missing_in_folder))
    print(len(extra_in_folder))


if __name__ == "__main__":
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json)
