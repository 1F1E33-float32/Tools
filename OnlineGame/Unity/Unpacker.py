# Reference: https://github.com/K0lb3/UnityPy/blob/master/UnityPy/tools/extractor.py

import argparse
import json
import os

import UnityPy
from tqdm import tqdm
from UnityPy.classes import Font, MonoBehaviour, Object, PPtr
from UnityPy.enums.ClassIDType import ClassIDType

UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.32f1"


def export_obj(obj, destination, append_name=False, append_path_id=False, export_unknown_as_typetree=False):
    data = obj.read()

    extend = EXPORT_TYPES.get(obj.type)
    if extend is None:
        if export_unknown_as_typetree:
            extend = exportMonoBehaviour
        else:
            return []

    fp = destination
    if append_name:
        name = data.m_Name if data.m_Name else data.object_reader.type.name
        fp = os.path.join(fp, name)

    base, ext = os.path.splitext(fp)
    if append_path_id:
        base = f"{base}_{data.object_reader.path_id}"
    return extend(data, base, ext)


def extract_assets(source, target, include_types=None, ignore_first_dirs=0, append_path_id=False, export_unknown_as_typetree=False):
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

    # 对过滤后的项目进行排序
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

        exports = export_obj(obj, dest_dir, append_path_id=append_path_id, export_unknown_as_typetree=export_unknown_as_typetree)

        exported.extend(exports)

    return exported


def exportTextAsset(obj, fp, extension=".bytes"):
    with open(f"{fp}{extension}", "wb") as f:
        f.write(obj.m_Script.encode("utf-8", "surrogateescape"))
    return [(obj.assets_file, obj.object_reader.path_id)]


def exportFont(obj: Font, fp, extension=""):
    if obj.m_FontData:
        extension = ".ttf"
        if obj.m_FontData[0:4] == b"OTTO":
            extension = ".otf"
        with open(f"{fp}{extension}", "wb") as f:
            f.write(bytes(obj.m_FontData))
    return [(obj.assets_file, obj.object_reader.path_id)]


def exportMesh(obj, fp, extension=".obj"):
    with open(f"{fp}{extension}", "wt", encoding="utf8", newline="") as f:
        f.write(obj.export())
    return [(obj.assets_file, obj.object_reader.path_id)]


def exportShader(obj, fp, extension=".txt"):
    with open(f"{fp}{extension}", "wt", encoding="utf8", newline="") as f:
        f.write(obj.export())
    return [(obj.assets_file, obj.object_reader.path_id)]


def exportMonoBehaviour(obj, fp, extension=""):
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


def exportAudioClip(obj, fp, extension=""):
    samples = obj.samples
    if len(samples) == 0:
        pass
    elif len(samples) == 1:
        with open(f"{fp}.wav", "wb") as f:
            f.write(list(samples.values())[0])
    else:
        os.makedirs(fp, exist_ok=True)
        for name, clip_data in samples.items():
            with open(os.path.join(fp, f"{name}.wav"), "wb") as f:
                f.write(clip_data)
    return [(obj.assets_file, obj.object_reader.path_id)]


def exportSprite(obj, fp, extension=".png"):
    obj.image.save(f"{fp}{extension}")
    exported = [(obj.assets_file, obj.object_reader.path_id), (obj.m_RD.texture.assetsfile, obj.m_RD.texture.path_id)]
    alpha_assets_file = getattr(obj.m_RD.alphaTexture, "assets_file", None)
    alpha_path_id = getattr(obj.m_RD.alphaTexture, "path_id", None)
    if alpha_path_id and alpha_assets_file:
        exported.append((alpha_assets_file, alpha_path_id))
    return exported


def exportTexture2D(obj, fp, extension=".png"):
    if obj.m_Width:
        obj.image.save(f"{fp}{extension}")
    return [(obj.assets_file, obj.object_reader.path_id)]


def exportGameObject(obj, fp, extension=""):
    exported = [(obj.assets_file, obj.object_reader.path_id)]
    refs = crawl_obj(obj)
    if refs:
        os.makedirs(fp, exist_ok=True)
    for ref_id, ref in refs.items():
        if (ref.assets_file, ref_id) in exported or ref.type == ClassIDType.GameObject:
            continue
        try:
            exported.extend(export_obj(ref, fp, True, True))
        except Exception as e:
            print(f"Failed to export {ref_id}")
            print(e)
    return exported


EXPORT_TYPES = {
    ClassIDType.GameObject: exportGameObject,
    ClassIDType.Sprite: exportSprite,
    ClassIDType.AudioClip: exportAudioClip,
    ClassIDType.Font: exportFont,
    ClassIDType.Mesh: exportMesh,
    ClassIDType.MonoBehaviour: exportMonoBehaviour,
    ClassIDType.Shader: exportShader,
    ClassIDType.TextAsset: exportTextAsset,
    ClassIDType.Texture2D: exportTexture2D,
}

MONOBEHAVIOUR_TYPETREES = {}


def crawl_obj(obj, ret=None):
    if not ret:
        ret = {}

    if isinstance(obj, PPtr):
        if obj.path_id == 0 and obj.file_id == 0 and obj.index == -2:
            return ret
        try:
            obj = obj.read()
        except AttributeError:
            return ret
    else:
        return ret
    ret[obj.path_id] = obj

    if isinstance(obj, (MonoBehaviour, Object)):
        data = obj.read_typetree().__dict__.values()
    else:
        data = obj.__dict__.values()

    for value in flatten(data):
        if isinstance(value, (Object, PPtr)):
            if value.path_id in ret:
                continue
            crawl_obj(value, ret)
    return ret


def flatten(target):
    for el in list(target):
        if isinstance(el, (list, tuple)):
            yield from flatten(el)
        elif isinstance(el, dict):
            yield from flatten(el.values())
        else:
            yield el


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Unity assets with fixed filtering logic.")
    parser.add_argument("--src", default=r"C:\Program Files (x86)\Steam\steamapps\common\HeavenBurnsRed\HeavenBurnsRed_Data\StreamingAssets\aa\StandaloneWindows64")
    parser.add_argument("--dst", default=r"C:\Users\bfloat16\Desktop\hbr\export")
    parser.add_argument("--id", default=True)
    parser.add_argument("--unknown", default=False)
    parser.add_argument("--ignore", type=int, default=0, metavar="N")
    parser.add_argument("--filter", nargs="+", default=["TextAsset"])
    args = parser.parse_args()

    exported = extract_assets(source=args.src, target=args.dst, include_types=args.filter, ignore_first_dirs=args.ignore, append_path_id=args.id, export_unknown_as_typetree=args.unknown)
