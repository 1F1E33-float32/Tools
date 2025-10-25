import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

import numpy as np


def case_insensitive_import(module_name: str):
    parts = module_name.split(".")
    module = None
    for idx, part in enumerate(parts):
        if idx == 0:
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
            if hasattr(parent, "__path__"):
                for finder, name, ispkg in pkgutil.iter_modules(parent.__path__):
                    if name.lower() == part.lower():
                        module = importlib.import_module(f"{parent.__name__}.{name}")
                        found = True
                        break
            if not found:
                raise ModuleNotFoundError(f"Module '{module_name}' not found (case-insensitive)")
    return module


def load_schema_module(file_stem: str):
    # e.g. SomeTableDBSchema.bytes -> Global.SomeTableExcel
    if file_stem.lower().endswith("dbschema"):
        excel_name = file_stem[:-8] + "Excel"
    else:
        excel_name = file_stem
    mod_name = f"Global.{excel_name}"
    try:
        return importlib.import_module(mod_name)
    except ModuleNotFoundError:
        try:
            return case_insensitive_import(mod_name)
        except ModuleNotFoundError:
            return None


def sanitize(value: Any):
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="ignore")
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.generic,)):
        return value.item()
    return value


def fb_to_dict(obj, root_cls) -> dict:
    out = {}
    # scalar-like getters (no args)
    for name, fn in inspect.getmembers(root_cls, inspect.isfunction):
        if name.startswith("_") or not name[0].isupper():
            continue
        if getattr(fn, "__code__", None) and fn.__code__.co_argcount == 1:
            try:
                val = getattr(obj, name)()
                out[name] = sanitize(val)
            except Exception:
                pass
    # vector-like getters (index arg)
    for name, fn in inspect.getmembers(root_cls, inspect.isfunction):
        if name.startswith("_") or not name[0].isupper():
            continue
        if getattr(fn, "__code__", None) and fn.__code__.co_argcount == 2:
            length_name = f"{name}Length"
            if hasattr(obj, length_name):
                try:
                    length = getattr(obj, length_name)()
                    items = []
                    for i in range(length):
                        try:
                            child = getattr(obj, name)(i)
                        except Exception:
                            continue
                        if hasattr(child, "__class__") and any(c for c in dir(child.__class__) if c and c[0].isupper()):
                            try:
                                items.append(fb_to_dict(child, child.__class__))
                            except Exception:
                                items.append(sanitize(child))
                        else:
                            items.append(sanitize(child))
                    out[name] = items
                except Exception:
                    pass
    return out


def deserialize_bytes_file(file_path: Path):
    stem = file_path.stem
    module = load_schema_module(stem)
    if not module:
        raise ValueError(f"Module not found: {stem}")
    root_name = module.__name__.split(".")[-1]
    root_cls = getattr(module, root_name, None)
    if root_cls is None:
        raise ValueError(f"Root class not found: {root_name}")
    # resolve GetRootAs function
    if hasattr(root_cls, "GetRootAs"):
        get_root_fn = getattr(root_cls, "GetRootAs")
    elif hasattr(root_cls, f"GetRootAs{root_name}"):
        get_root_fn = getattr(root_cls, f"GetRootAs{root_name}")
    else:
        raise ValueError(f"GetRootAs function not found: {root_name}")
    data = file_path.read_bytes()
    try:
        fb_obj = get_root_fn(data, 0)
    except TypeError:
        try:
            fb_obj = get_root_fn(data)
        except TypeError:
            fb_obj = get_root_fn(bytearray(data), 0)
    return [fb_to_dict(fb_obj, root_cls)]
