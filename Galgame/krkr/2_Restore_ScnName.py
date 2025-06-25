import os
import json
import argparse
import shutil

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\GAL\2025_04\Role player Ikura Shimai no Nenmaku Portrait - Gurigucha LIVE!\Extractor_Output\data")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_galgame\script")
    return parser.parse_args(args=args, namespace=namespace)

def read_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def main(JA_dir, op_dir):
    files_original = []
    for root, dirs, files in os.walk(JA_dir):
        for f in files:
            if f.endswith('.json') and not f.endswith('.resx.json'):
                files_original.append(os.path.join(root, f))

    for filepath in files_original:
        # 直接用 filepath，无需再拼接 JA_dir
        _0_JA_data = read_json_file(filepath)

        if 'scenes' in _0_JA_data and 'name' in _0_JA_data:
            json_name = _0_JA_data['name']
            os.makedirs(op_dir, exist_ok=True)
            # 构造新文件名，目标目录为 op_dir
            new_file_path = os.path.join(op_dir, json_name + ".json")
            try:
                shutil.move(filepath, new_file_path)
                print(f"Renamed: {filepath} -> {new_file_path}")
            except Exception as e:
                print(f"Failed to rename {filepath}: {e}")

if __name__ == '__main__':
    cmd = parse_args()
    main(cmd.JA, cmd.op)