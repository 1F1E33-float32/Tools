import os, json, shutil, argparse

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument('--audio_ext', default='.ogg')
    p.add_argument('--audio_dir',  default=r"D:\Fuck_galgame\voice")
    p.add_argument('--index_json', default=r"D:\Fuck_galgame\index.json")
    p.add_argument('--out_dir',    default=r"D:\Dataset_VN\Milk Factory_Motto! Haramase! Honoo no Oppai Isekai Oppai Bunny Gakuen!")
    return p.parse_args(args=args, namespace=namespace)

def main(audio_ext, audio_dir, index_path, out_dir):
    # 1. 收集所有 .ogg 文件
    audio_map = {}
    for root, _, files in os.walk(audio_dir):
        for f in files:
            if f.lower().endswith(audio_ext):
                name = os.path.splitext(f)[0]
                audio_map[name] = os.path.join(root, f)

    # 2. 读取 index.json
    with open(index_path, encoding='utf-8') as fp:
        data = json.load(fp)

    # 3. 过滤：Voice 为 None 或者 找得到对应音频的保留
    new_data = []
    for rec in data:
        v = rec.get('Voice')
        if v is None or v in audio_map:
            new_data.append(rec)
        else:
            print(f"跳过，找不到音频: Voice={v}")

    # 3.5. 给每条有 Voice 的记录都加上扩展名
    for rec in new_data:
        v = rec.get('Voice')
        if v is not None:
            rec['Voice'] = v + audio_ext

    # 4. 把音频拷贝到 out_dir/{Speaker}/{Voice}
    for rec in new_data:
        v = rec.get('Voice')
        sp = rec.get('Speaker')
        if v:
            dst_dir = os.path.join(out_dir, sp or '')
            os.makedirs(dst_dir, exist_ok=True)
            src = audio_map[os.path.splitext(v)[0]]
            dst = os.path.join(dst_dir, v)
            shutil.copy2(src, dst)

    # 5. 写新的 index.json
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.json'), 'w', encoding='utf-8') as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)