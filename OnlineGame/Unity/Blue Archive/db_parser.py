import argparse
import json
import sqlite3
from pathlib import Path

from fbs_parser import deserialize_bytes_file


def dump_table(conn: sqlite3.Connection, table: str, out_dir: Path):
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]  # cid, name, type, notnull, dflt_value, pk
    has_bytes = any(c.lower() == "bytes" for c in cols)

    cur = conn.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()

    # Prepare output path
    out_path = out_dir / f"{table}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_items = []
    for row in rows:
        item = {}
        blob_json = None
        for col_name, value in zip(cols, row):
            if has_bytes and col_name.lower() == "bytes" and value is not None:
                if isinstance(value, memoryview):
                    data = bytes(value)
                else:
                    data = value
                bytes_path = out_dir / f"{table}.bytes"
                bytes_path.write_bytes(data)
                records = deserialize_bytes_file(bytes_path)
                blob_json = records
            else:
                if isinstance(value, bytes):
                    item[col_name] = value.decode("utf-8", errors="ignore")
                else:
                    item[col_name] = value
        if blob_json is not None:
            item["Parsed"] = blob_json
        out_items.append(item)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out_items, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db_path", default=r"C:\Program Files (x86)\Steam\steamapps\common\BlueArchive\BlueArchive_Data\StreamingAssets\PUB\Resource\Preload\TableBundles\ExcelDB.db")
    ap.add_argument("--output_dir", default=r"C:\Program Files (x86)\Steam\steamapps\common\BlueArchive\BlueArchive_Data\StreamingAssets\PUB\Resource\Preload\TableBundles\ExcelDB.json")
    args = ap.parse_args()

    db_path = Path(args.db_path)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%DBSchema%'")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        dump_table(conn, t, out_dir)
        print(f"已导出: {t}")


if __name__ == "__main__":
    main()
