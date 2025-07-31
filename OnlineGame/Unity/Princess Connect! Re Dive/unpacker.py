import os
import argparse
from tqdm import tqdm

import UnityPy
from UnityPy.enums.ClassIDType import ClassIDType
from UnityPy.environment import Environment

def exportTextAsset(obj, fp, extension=".bytes"):
    with open(f"{fp}{extension}", "wb") as f:
        f.write(obj.m_Script.encode("utf-8", "surrogateescape"))
    return [(obj.assets_file, obj.object_reader.path_id)]

EXPORT_TYPES = {
    ClassIDType.TextAsset: exportTextAsset,
}

UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.45f1"

def _custom_load_folder(self, path):
    files_to_load = []
    for root, dirs, files in self.fs.walk(path):
        for fname in files:
            low = fname.lower()
            if low.endswith(".unity3d") and "storydata" in low:
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
        if not obj_path.startswith('assets/_elementsresources/resources/storydata/data'):
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
    parser.add_argument("--src", default=r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\RAW\a")
    parser.add_argument("--dst", default=r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\EXP\Story")
    parser.add_argument("--id", default=True)
    parser.add_argument("--ignore", type=int, default=5, metavar="N")
    parser.add_argument("--filter", nargs="+", default=["TextAsset"])
    args = parser.parse_args()

    exported = extract_assets(source=args.src, target=args.dst, include_types=args.filter, ignore_first_dirs=args.ignore, append_path_id=args.id)