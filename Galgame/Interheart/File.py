import os
import json
import shutil
import argparse
from tqdm import tqdm
import av

# 新增：获取音频时长（秒）
def get_audio_duration(path: str) -> float:
    container = av.open(path, metadata_errors="ignore")
    # container.duration 单位是 AV_TIME_BASE (1e6)
    if container.duration is not None:
        time =  container.duration / 1_000_000
        container.close()
        return time

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument('--audio_ext', default='.ogg')
    p.add_argument('--audio_dir',  default=r"D:\Fuck_galgame\voice")
    p.add_argument('--index_json', default=r"D:\Fuck_galgame\index.json")
    p.add_argument('--out_dir',    default=r"D:\Dataset_VN_NoScene\Interheart Glossy_Hara Katsu! 3 ~Kozukuri Business Haigyou no Kiki!~")
    return p.parse_args(args=args, namespace=namespace)

def main(audio_ext, audio_dir, index_path, out_dir):
    # 1. 收集所有音频文件，键为小写文件名（不含扩展名）
    audio_map = {}
    for root, _, files in os.walk(audio_dir):
        for f in files:
            if f.lower().endswith(audio_ext.lower()):
                name_lower = os.path.splitext(f)[0].lower()
                audio_map[name_lower] = os.path.join(root, f)

    # 2. 读取 index.json
    with open(index_path, encoding='utf-8') as fp:
        data = json.load(fp)

    # 3. 过滤：Voice 为 None 或者 对应音频存在
    new_data = []
    for rec in data:
        v = rec.get('Voice')
        if v is None:
            new_data.append(rec)
        else:
            v_lower = v.lower()
            if v_lower in audio_map:
                rec_copy = rec.copy()
                rec_copy['Voice'] = v_lower + audio_ext.lower()
                new_data.append(rec_copy)
            else:
                print(f"跳过，找不到音频: Voice={v}")

    # 4. 检查音频时长并移动；时长异常或获取失败则跳过
    final_data = []
    for rec in tqdm(new_data, desc="Checking duration and moving"):  # type: ignore
        v = rec.get('Voice')
        sp = rec.get('Speaker')
        src = os.path.join(audio_dir, rec['Folder'], rec['Voice'])
        try:
            duration = get_audio_duration(src)
        except Exception as e:
            print(f"跳过，无法获取时长: Voice={rec['Voice']}, 错误: {e}")
            continue
        # 根据需要调整时长阈值，比如 > 0 或 > 0.1 秒
        if duration > 0:
            dst_dir = os.path.join(out_dir, sp)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, rec['Voice'])
            shutil.move(src, dst)
            final_data.append(rec)
        else:
            print(f"跳过，时长异常 (duration={duration}s): Voice={rec['Voice']}")

    # 用通过时长检查的数据替换 new_data
    new_data = final_data

    # 5. 写新的 index.json（移除 Folder 字段）
    for rec in new_data:
        rec.pop('Folder', None)

    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, 'index.json')
    with open(index_out, 'w', encoding='utf-8') as fp:
        json.dump(new_data, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.audio_ext, args.audio_dir, args.index_json, args.out_dir)