import os
import json
import shutil
import argparse
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument('--audio_ext',  default='.ogg')
    p.add_argument('--audio_dir',  default=r"D:\\Fuck_galgame\\voice")
    p.add_argument('--index_json', default=r"D:\\Fuck_galgame\\index.json")
    p.add_argument('--out_dir',    default=r"D:\Dataset_VN_NoScene\HOOKSOFT_E School Life")
    return p.parse_args(args=args, namespace=namespace)

def main(audio_ext, audio_dir, index_path, out_dir):
    # Normalize extension: ensure leading dot
    if audio_ext and not audio_ext.startswith('.'):
        audio_ext = '.' + audio_ext

    # 1. Collect all audio files, keyed by lowercase name without extension
    audio_map = {}
    for root, _, files in os.walk(audio_dir):
        for f in files:
            name_lower = os.path.splitext(f)[0].lower()
            audio_map[name_lower] = os.path.join(root, f)

    # 2. Load index.json
    with open(index_path, encoding='utf-8') as fp:
        data = json.load(fp)

    # 3. Filter and update Voice entries (assumes Voice has no extension)
    new_data = []
    for rec in data:
        v = rec.get('Voice')
        if not v:
            new_data.append(rec)
            continue

        v_lower = v.lower()
        if v_lower in audio_map:
            rec_copy = rec.copy()
            rec_copy['Voice'] = v_lower + audio_ext.lower()
            new_data.append(rec_copy)
        else:
            print(f"Skipping, audio not found: Voice={v}")

    # 4. Copy audio files with new extension to out_dir/Speaker/Voice
    for rec in tqdm(new_data, ncols=150):
        voice = rec.get('Voice')
        speaker = rec.get('Speaker') or ''
        if not voice:
            continue
        dst_dir = os.path.join(out_dir, speaker)
        os.makedirs(dst_dir, exist_ok=True)
        name_no_ext = os.path.splitext(voice)[0]
        src_path = audio_map.get(name_no_ext)
        if src_path:
            dst_path = os.path.join(dst_dir, voice)
            shutil.copy2(src_path, dst_path)
        else:
            print(f"Warning: source file not found for {name_no_ext}")

    # 5. Write new index.json in output directory
    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, 'index.json')
    with open(index_out, 'w', encoding='utf-8') as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)