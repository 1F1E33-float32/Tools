import os
import json
import shutil
from tqdm import tqdm

input_json_filepath = r'D:\Fuck_galgame\index.json'
source_folder = r"D:\Fuck_galgame\OVK"
output_folder = r"D:\Dataset_VN_NoScene\Studio Momoka_Ore no Kanojo ga Gachi Hentai Sugiru"

with open(input_json_filepath, 'r', encoding='utf-8') as file:
    dialogues = json.load(file)

# 构建文件映射
file_mapping = {}
for root, _, files in os.walk(source_folder):
    for filename in files:
        name, ext = os.path.splitext(filename)
        folder_name = os.path.basename(root)
        if ext.lower() == '.ogg':  # 假设我们只关心 .ogg 文件
            key = f"{folder_name.lower()}#{int(name):05d}"
            file_mapping[key] = os.path.join(root, filename)

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

output_data = []
for dialogue in tqdm(dialogues):
    voice = dialogue['Voice']
    folder_name, file_id = voice.split('#')
    file_id = f"{int(file_id):05d}"  # 将文件 ID 转换为整数并格式化为 5 位数
    key = f"{folder_name.lower()}#{file_id}"
    
    if key in file_mapping:
        src_path = file_mapping[key]
        
        # 创建以 Speaker 命名的子文件夹
        speaker_folder = os.path.join(output_folder, dialogue['Speaker'])
        if not os.path.exists(speaker_folder):
            os.makedirs(speaker_folder)
        
        relative_path = os.path.join(output_folder, dialogue['Speaker'], f"{key}.ogg")
        shutil.move(src_path, relative_path)
        
        output_data.append({
            'Speaker': dialogue['Speaker'],
            'Text': dialogue['Text'],
            'Voice': key + '.ogg',
        })

output_json_filepath = os.path.join(output_folder, 'index.json')
with open(output_json_filepath, 'w', encoding='utf-8') as file:
    json.dump(output_data, file, ensure_ascii=False, indent=4)