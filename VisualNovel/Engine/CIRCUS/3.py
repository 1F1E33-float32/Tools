import os
import json
import shutil

audio_root = r'D:\Fuck_galgame'
output_root = r'D:\Fuck_galgame\f_'

with open(r'D:\Fuck_galgame\index.json', 'r', encoding='utf-8') as f:
    index_data = json.load(f)

audio_cache = {}
for root, dirs, files in os.walk(audio_root):
    for file in files:
        # 获取相对路径并标准化
        rel_path = os.path.relpath(os.path.join(root, file), audio_root)
        # 使用小写路径作为键
        audio_cache[rel_path.lower()] = os.path.join(root, file)

# 处理后的新数据
processed_data = []

for entry in index_data:
    speaker = entry['Speaker']
    voice_path = entry['Voice']
    
    # 标准化路径格式并转换为小写
    normalized_path = voice_path.replace('/', os.sep).replace('\\', os.sep).lower()
    
    # 查找实际文件路径
    if normalized_path in audio_cache:
        src_path = audio_cache[normalized_path]
        
        # 创建角色目录
        speaker_dir = os.path.join(output_root, speaker)
        os.makedirs(speaker_dir, exist_ok=True)
        
        # 复制文件到新目录
        filename = os.path.basename(src_path)
        dest_path = os.path.join(speaker_dir, filename)
        shutil.copy(src_path, dest_path)
        
        # 更新路径记录
        entry['Voice'] = f"{filename}"
        processed_data.append(entry)
    else:
        print(f"找不到文件: {voice_path}")

# 保存新 index.json
output_index = os.path.join(output_root, 'index.json')
with open(output_index, 'w', encoding='utf-8') as f:
    json.dump(processed_data, f, ensure_ascii=False, indent=2)

print("文件整理完成，新索引已保存至:", output_index)