import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\scenario")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("／", "")
    return text


def _read_name_dict(scene_db_path: Path) -> Dict[int, str]:
    conn = sqlite3.connect(scene_db_path.as_posix())
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM name")
        name_dict: Dict[int, str] = {}
        for row in cur.fetchall():
            try:
                key = int(row["id"]) if row["id"] is not None else None
            except Exception:
                # Fallback if row keys are positional
                key = int(row[0]) if row[0] is not None else None
            value = row["name"] if "name" in row.keys() else row[1]
            if key is not None:
                name_dict[key] = value
        return name_dict
    finally:
        conn.close()


def _iter_text_rows(scenedata_db_path: Path) -> Iterable[sqlite3.Row]:
    conn = sqlite3.connect(scenedata_db_path.as_posix())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Read minimally required fields; ordering for stability
        cur.execute("SELECT name, voice, text FROM text ORDER BY scene, idx")
        for row in cur:
            yield row
    finally:
        conn.close()


def main(JA_dir: str, op_json: str):
    base = Path(JA_dir)
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Input folder not found: {base}")

    scene_db = base / "scene.sdb"
    scenedata_db = base / "scenedata.sdb"

    name_dict = _read_name_dict(scene_db)

    fixed_results: List[Tuple[str, int, str, str]] = []
    for row in _iter_text_rows(scenedata_db):
        name_id = row["name"] if "name" in row.keys() else row[0]
        try:
            name_id_int = int(name_id) if name_id is not None else 0
        except Exception:
            # If non-integer, skip
            continue
        if name_id_int == 0:
            continue
        speaker = name_dict.get(name_id_int)
        if not speaker:
            continue
        voice = row["voice"] if "voice" in row.keys() else row[1]
        # Skip rows where voice is None per requirement
        if voice is None:
            continue
        text = row["text"] if "text" in row.keys() else row[2]
        # Skip rows where text is None per requirement
        if text is None:
            continue
        text = text_cleaning(text)
        fixed_results.append((speaker, name_id_int, str(voice), text))

    output_path = Path(op_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", encoding="utf-8") as file:
        seen = set()
        json_data = []
        for Speaker, Speaker_id, Voice, Text in fixed_results:
            if Voice in seen:
                continue
            seen.add(Voice)
            json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op)
