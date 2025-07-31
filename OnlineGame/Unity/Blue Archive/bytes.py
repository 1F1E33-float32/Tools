import flatbuffers
import importlib
import inspect
import json
import pkgutil
import sys
from pathlib import Path
from typing import Any, Iterator, List

import numpy as np  # gracefully handle ndarray values

# === CONFIG ===
INPUT_DIR = Path(r"D:\VMware\steamapps\common\BlueArchive\BlueArchive_Data\StreamingAssets\PUB\Resource\Preload\TableBundles\Excel_dec")  # folder containing *.byets files
OUTPUT_DIR = Path("deserialized_json2")  # output directory for JSON files
# ==============

# Ensure output directory exists
output_dir = OUTPUT_DIR
output_dir.mkdir(exist_ok=True)

def case_insensitive_import(module_name: str):
    """
    Import a module by name, ignoring case. Works by scanning the package's __path__.
    """
    parts = module_name.split('.')
    module = None
    for idx, part in enumerate(parts):
        if idx == 0:
            # top-level import
            try:
                module = importlib.import_module(part)
                continue
            except ModuleNotFoundError:
                for finder, name, ispkg in pkgutil.iter_modules():
                    if name.lower() == part.lower():
                        module = importlib.import_module(name)
                        break
                if not module:
                    raise ModuleNotFoundError(f"Module '{part}' not found (case-insensitive)")
        else:
            parent = module
            found = False
            if hasattr(parent, '__path__'):
                for finder, name, ispkg in pkgutil.iter_modules(parent.__path__):
                    if name.lower() == part.lower():
                        module = importlib.import_module(f"{parent.__name__}.{name}")
                        found = True
                        break
            if not found:
                raise ModuleNotFoundError(f"Module '{module_name}' not found (case-insensitive)")
    return module


def load_schema_module(file_stem: str):
    """
    Import the corresponding Excel flatbuffers module for a given bytes filename stem.
    E.g. 'CharacterDBSchema' -> 'Global.CharacterExcel'.
    """
    # Replace 'DBSchema' with 'Excel' in the file stem, case-insensitive
    if file_stem.lower().endswith('dbschema'):
        excel_name = file_stem[:-8] + 'Excel'
    else:
        excel_name = file_stem
    mod_name = f"Global.{excel_name}"
    try:
        return importlib.import_module(mod_name)
    except ModuleNotFoundError:
        try:
            return case_insensitive_import(mod_name)
        except ModuleNotFoundError:
            print(f"⚠️  Schema module '{mod_name}' not found — skipping {file_stem}.")
            return None


def sanitize(value: Any):
    """Convert non-JSON-serializable types to plain Python equivalents."""
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="ignore")
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.generic,)):
        return value.item()
    return value


def fb_to_dict(obj, root_cls) -> dict:
    """Convert a flatbuffers object into a plain dict via reflection on generated accessors, including vectors."""
    out = {}
    # Handle scalar fields
    for name, fn in inspect.getmembers(root_cls, inspect.isfunction):
        if name.startswith("_") or not name[0].isupper():
            continue
        # zero-argument getters
        if fn.__code__.co_argcount == 1:
            try:
                val = getattr(obj, name)()
                out[name] = sanitize(val)
            except Exception:
                pass
    # Handle vector fields (methods taking index)
    for name, fn in inspect.getmembers(root_cls, inspect.isfunction):
        if name.startswith("_") or not name[0].isupper():
            continue
        # two-argument accessors for vectors
        if fn.__code__.co_argcount == 2:
            length_name = f"{name}Length"
            if hasattr(obj, length_name):
                try:
                    length = getattr(obj, length_name)()
                    items = []
                    for i in range(length):
                        child = getattr(obj, name)(i)
                        # recurse: determine child's class
                        child_cls = child.__class__
                        items.append(fb_to_dict(child, child_cls))
                    out[name] = items
                except Exception:
                    pass
    return out
    """Convert a flatbuffers object into a plain dict via reflection on generated accessors."""
    out = {}
    for name, fn in inspect.getmembers(root_cls, inspect.isfunction):
        if name.startswith("_") or not name[0].isupper() or fn.__code__.co_argcount != 1:
            continue
        try:
            val = getattr(obj, name)()
            out[name] = sanitize(val)
        except Exception:
            # tolerate fields that can't be read (unions, deprecated, etc.)
            pass
    return out


def deserialize_bytes_file(file_path: Path) -> List[dict]:
    """Deserialize a .byets file using its FlatBuffers schema module."""
    stem = file_path.stem
    module = load_schema_module(stem)
    if not module:
        return []
    # Get root class
    root_name = module.__name__.split('.')[-1]
    root_cls = getattr(module, root_name)
    # Determine get_root function dynamically
    if hasattr(root_cls, "GetRootAs"):
        get_root_fn = getattr(root_cls, "GetRootAs")
    else:
        get_root_fn = getattr(root_cls, f"GetRootAs{root_name}")
    # Read data
    data = file_path.read_bytes()
    if not data:
        return []
    # Try calling GetRootAs with flexible signature
    try:
        fb_obj = get_root_fn(data)
    except TypeError:
        fb_obj = get_root_fn(bytearray(data), 0)
    # Convert to dict
    return [fb_to_dict(fb_obj, root_cls)]

def main(input_dir: Path = INPUT_DIR):
    for file_path in input_dir.glob('*.bytes'):
        print(f"▶ Processing {file_path.name} …")
        records = deserialize_bytes_file(file_path)
        if not records:
            continue
        out_file = OUTPUT_DIR / f"{file_path.stem}.json"  # preserve original stem
        with out_file.open("w", encoding="utf-8") as fp:
            json.dump(records, fp, ensure_ascii=False, indent=4)
        print(f"   → {out_file}  ({len(records)} entries)")

    print("✔ All files processed.")

if __name__ == "__main__":
    main()