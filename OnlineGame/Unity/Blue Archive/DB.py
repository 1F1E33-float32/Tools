import flatbuffers
import importlib
import inspect
import json
import sqlite3
from pathlib import Path
from typing import Iterator, List, Any

import numpy as np  # new ➜ handle ndarray values gracefully

# === CONFIG ===
DB_PATH = r"D:\VMware\steamapps\common\BlueArchive\BlueArchive_Data\StreamingAssets\PUB\Resource\Preload\TableBundles\ExcelDB.db"  # <- adjust if needed
OUTPUT_DIR = Path("deserialized_json")
# ==============

OUTPUT_DIR.mkdir(exist_ok=True)


def iter_tables(conn: sqlite3.Connection) -> Iterator[str]:
    """Yield every table name in the SQLite database."""
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    yield from (row[0] for row in cur.fetchall())


def blob_col_index(conn: sqlite3.Connection, table: str) -> int:
    """Return the column index (0‑based) of the first BLOB column; fallback to 1 (Blue Archive convention)."""
    for cid, _name, ctype, *_ in conn.execute(f"PRAGMA table_info([{table}]);"):
        if (ctype or "").upper() == "BLOB":
            return cid
    return 1  # sensible default


def load_schema_module(table: str):
    """Import the corresponding *Excel* flatbuffers module for a given *DBSchema* table."""
    if "DBSchema" not in table:
        return None
    mod_name = f"Global.{table.replace('DBSchema', 'Excel')}"
    try:
        return importlib.import_module(mod_name)
    except ModuleNotFoundError:
        print(f"⚠️  Schema module '{mod_name}' not found — skipping {table}.")
        return None


def get_root_api(module):
    """Return (<root_class>, <get_root_function>) tuple from the schema module."""
    root_name = module.__name__.split(".")[-1]
    root_cls = getattr(module, root_name)
    get_fn = getattr(root_cls, f"GetRootAs{root_name}")
    return root_cls, get_fn


def sanitize(value: Any):
    """Convert non‑JSON‑serializable types to plain Python equivalents."""
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="ignore")
    if isinstance(value, np.ndarray):
        return value.tolist()
    # numpy scalar → Python scalar (e.g., np.int32 → int)
    if isinstance(value, (np.generic,)):
        return value.item()
    return value


def fb_to_dict(obj, root_cls) -> dict:
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


def deserialize_table(conn: sqlite3.Connection, table: str, module) -> List[dict]:
    """Deserialize every row of *table* using its FB schema."""
    idx = blob_col_index(conn, table)
    root_cls, get_root = get_root_api(module)
    data = []
    for row in conn.execute(f"SELECT * FROM [{table}];"):
        blob = row[idx]
        if not blob:
            continue
        obj = get_root(bytearray(blob), 0)
        data.append(fb_to_dict(obj, root_cls))
    return data


def main(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    for table in iter_tables(conn):
        schema_module = load_schema_module(table)
        if not schema_module:
            continue

        print(f"\u25B6 Processing {table} …")
        records = deserialize_table(conn, table, schema_module)

        out_file = OUTPUT_DIR / f"{table.replace('DBSchema', '')}.json"
        with out_file.open("w", encoding="utf-8") as fp:
            json.dump(records, fp, ensure_ascii=False, indent=4)
        print(f"   → {out_file}  ({len(records)} rows)")

    conn.close()
    print("✔ All tables processed.")


if __name__ == "__main__":
    main()
