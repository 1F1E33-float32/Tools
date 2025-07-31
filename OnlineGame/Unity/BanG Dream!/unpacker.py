import os
import json
import argparse
from tqdm import tqdm

import UnityPy
from UnityPy.enums.ClassIDType import ClassIDType
from UnityPy.environment import Environment
from UnityPy.classes import MonoBehaviour

MONOBEHAVIOUR_TYPETREES = {}

UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.39f1"

def exportTextAsset(obj, fp, extension=".bytes"):
    with open(f"{fp}", "wb") as f:
        f.write(obj.m_Script.encode("utf-8", "surrogateescape"))
    return [(obj.assets_file, obj.object_reader.path_id)]

def exportMonoBehaviour(obj, fp, extension= ""):
    export = None
    if obj.object_reader.serialized_type.node:
        export = obj.object_reader.read_typetree()
    elif isinstance(obj, MonoBehaviour):
        script_ptr = obj.m_Script
        if script_ptr:
            script = script_ptr.read()
            nodes = MONOBEHAVIOUR_TYPETREES.get(script.m_AssemblyName, {}).get(script.m_ClassName, None)
            if nodes:
                export = obj.object_reader.read_typetree(nodes)
    else:
        export = obj.object_reader.read_typetree()

    if not export:
        extension = ".bin"
        export = obj.object_reader.raw_data
    else:
        extension = ".json"
        export = json.dumps(export, indent=4, ensure_ascii=False).encode("utf8", errors="surrogateescape")
    with open(f"{fp}{extension}", "wb") as f:
        f.write(export)
    return [(obj.assets_file, obj.object_reader.path_id)]

EXPORT_TYPES = {
    ClassIDType.MonoBehaviour: exportMonoBehaviour,
    ClassIDType.TextAsset: exportTextAsset,
}

def _custom_load_folder(self, path):
    files_to_load = []
    for root, dirs, files in self.fs.walk(path):
        for fname in files:
            low = fname.lower()
            if low.endswith(".unity3d"):
                files_to_load.append(self.fs.sep.join([root, fname]))
    self.load_files(files_to_load)

Environment.load_folder = _custom_load_folder

def export_obj(obj, destination, append_name=False, append_path_id=False):
    data = obj.read()

    extend = EXPORT_TYPES.get(obj.type)
    if extend is None:
            return []

    fp = destination
    if append_name:
        name = data.m_Name if data.m_Name else data.object_reader.type.name
        fp = os.path.join(fp, name)

    base, ext = os.path.splitext(fp)
    if append_path_id:
        base = f"{base}_{data.object_reader.path_id}"
    return extend(data, base, ext)

def extract_assets(source, target, include_types=None, ignore_first_dirs=0, append_path_id=False):
    print("Loading Unity Environment...")
    env = UnityPy.load(source)
    exported = []

    type_order = list(EXPORT_TYPES.keys())
    
    def order_key(item):
        if item[1].type in type_order:
            idx = type_order.index(item[1].type)
        else:
            idx = len(type_order)
        return idx
    
    print("Filtering and sorting items...")
    filtered_items = []
    for item in env.container.items():
        if item[1].m_PathID == 0:
            print(f"警告: 发现 m_PathID 为 0 的项目: {item[0]}")
            continue
        filtered_items.append(item)

    sorted_items = sorted(filtered_items, key=order_key)
    
    for obj_path, obj in tqdm(sorted_items, ncols=150):
        if include_types and obj.type.name not in include_types:
            continue
        parts = obj_path.split("/")[ignore_first_dirs:]
        
        filtered_parts = []
        for p in parts:
            if p:
                filtered_parts.append(p)
        
        dest_dir = os.path.join(target, *filtered_parts)
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        exports = export_obj(obj, dest_dir, append_path_id=append_path_id)
        exported.extend(exports)

    return exported

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=r"E:\Game_Dataset\jp.co.craftegg.band\RAW")
    parser.add_argument("--dst", default=r"E:\Game_Dataset\jp.co.craftegg.band\EXP")
    args = parser.parse_args()

    source = os.path.join(args.src, "scenario")
    dst = os.path.join(args.dst, "Story")
    exported = extract_assets(source=source, target=dst, include_types=["MonoBehaviour"], ignore_first_dirs=5, append_path_id=True)

    source = os.path.join(args.src, "sound")
    dst = os.path.join(args.dst, "Sound")
    exported = extract_assets(source=source, target=dst, include_types=["TextAsset"], ignore_first_dirs=5, append_path_id=False)