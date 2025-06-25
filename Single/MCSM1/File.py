import os
import json
import shutil
import argparse
import av  # PyAV for decoding check

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument('--audio_ext', default='.mp3')
    p.add_argument('--audio_dir',  default=r"D:\Games\MinecraftStoryMode Season1\fsb5_dec")
    p.add_argument('--index_json', default=r"D:\Games\MinecraftStoryMode Season1\archives_dec\index.json")
    p.add_argument('--out_dir',    default=r"D:\Dataset_VN\Telltale_MinecraftStoryMode Season1")
    return p.parse_args(args=args, namespace=namespace)

def main(audio_ext, audio_dir, index_path, out_dir):
    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)

    # 1. 构建 audio_map
    audio_map = {}
    for root, _, files in os.walk(audio_dir):
        base = os.path.basename(root)
        for f in files:
            if f.lower().endswith(audio_ext):
                vid = str(os.path.splitext(f)[0])
                audio_map.setdefault(vid, []).append({
                    'folder': base,
                    'path': os.path.join(root, f)
                })

    # 2. 读取原始 index.json
    with open(index_path, encoding='utf-8') as fp:
        data = json.load(fp)

    # 3. 去重 JESSE
    remove_idx = set()
    for i, rec in enumerate(data):
        if rec.get('Speaker') == 'JESSE':
            text0 = rec.get('Text')
            for j in range(i + 1, min(i + 10, len(data))):
                r2 = data[j]
                if (r2.get('Speaker') == 'JESSE' and r2.get('Text') == text0 and str(r2.get('Voice')) not in audio_map):
                    remove_idx.add(j)
                    print(f"删除 JESSE 重复记录: {text0} (索引 {j})")
    data = [r for idx, r in enumerate(data) if idx not in remove_idx]

    # 4. 校验 Voice，不在则置 None
    for rec in data:
        voice = rec.get('Voice')
        if voice is None or str(voice) not in audio_map:
            rec['Voice'] = None

    # 5. 拆分 JESSE 为男女声，并为每条记录新增绝对路径，其他 Speaker 多文件则报错
    new_data = []
    for rec in data:
        speaker = rec.get('Speaker')
        vid = rec.get('Voice')
        if vid and str(vid) in audio_map:
            entries = audio_map[str(vid)]
            if speaker == 'JESSE':
                # JESSE 性别分流
                for entry in entries:
                    folder = entry['folder']
                    src_path = entry['path']
                    if 'JesseMale' in folder:
                        new_speaker = 'JESSE_MALE'
                    elif 'JesseMale' not in folder:
                        new_speaker = 'JESSE_FEMALE'
                    else:
                        raise RuntimeError(f"未知 JESSE 文件夹: {folder}")
                    new_rec = rec.copy()
                    new_rec['Speaker'] = new_speaker
                    # Voice 保持原 vid 不变
                    # 新增绝对路径字段用于复制
                    new_rec['AudioPath'] = src_path
                    new_data.append(new_rec)
            else:
                # 其他 Speaker，如果有多条音频，抛错
                if len(entries) > 1:
                    raise RuntimeError(f"Speaker '{speaker}' 对应到多个音频文件: {entries}")
                entry = entries[0]
                new_rec = rec.copy()
                new_rec['AudioPath'] = entry['path']
                new_data.append(new_rec)
        else:
            new_data.append(rec)
    data = new_data

    # 6. 复制音频并校验解码
    for rec in data:
        audio_path = rec.get('AudioPath')
        if not audio_path:
            continue
        try:
            container = av.open(audio_path)
            # 尝试解码第一帧以检测合法性
            for packet in container.demux():
                for frame in packet.decode():
                    break
                break
        except Exception as e:
            print(f"解码失败，设置 Voice=None：{audio_path} -> {e}")
            rec['Voice'] = None
            continue
        # 复制文件
        rel_dst = os.path.relpath(audio_path, audio_dir)
        dst = os.path.join(out_dir, rel_dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(audio_path, dst)

    # 7. 写入处理后的 index.json (不包含 AudioPath 字段)
    out_index = os.path.join(out_dir, 'index.json')
    # 去除内部字段
    write_data = []
    for rec in data:
        rec_copy = {k: v for k, v in rec.items() if k != 'AudioPath'}
        write_data.append(rec_copy)
    with open(out_index, 'w', encoding='utf-8') as fp:
        json.dump(write_data, fp, ensure_ascii=False, indent=2)
    print(f"已写入处理后的 index.json 到 {out_index}")

if __name__ == '__main__':
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)