import argparse
import json
import os
import re
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import apsw
import UnityPy
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

PROGRESS_COLUMNS = (
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(bar_width=80),
    "[progress.percentage]{task.percentage:>6.2f}%",
    TextColumn("{task.completed}/{task.total}"),
    TimeElapsedColumn(),
    "•",
    TimeRemainingColumn(),
)

STORY_PATTERN = re.compile(r"story/data/\d+/\d+/storytimeline_\d+", re.IGNORECASE)
HOME_PATTERN = re.compile(r"home/data/(\d+)/(\d+)/hometimeline_\1_\2_\d+", re.IGNORECASE)
RACE_PATTERN = re.compile(r"race/storyrace/text/storyrace_\d+", re.IGNORECASE)
TARGET_FIELDS = ("VoiceSheetId", "CueId", "CharaId", "Name", "Text")

DEFAULT_DATABASE_KEY = bytes(
    [
        0x9C,
        0x2B,
        0xAB,
        0x97,
        0xBC,
        0xF8,
        0xC0,
        0xC4,
        0xF1,
        0xA9,
        0xEA,
        0x78,
        0x81,
        0xA2,
        0x13,
        0xF6,
        0xC9,
        0xEB,
        0xF9,
        0xD8,
        0xD4,
        0xC6,
        0xA8,
        0xE4,
        0x3C,
        0xE5,
        0xA2,
        0x59,
        0xBD,
        0xE7,
        0xE9,
        0xFD,
    ]
)
DEFAULT_CIPHER_NAME = "chacha20"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", dest="data_dir", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/RAW")
    parser.add_argument("--EXP", dest="output_dir", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/EXP")
    parser.add_argument("--thread", type=int, default=1 or 1)
    parser.add_argument("--meta", dest="meta_path", default=r"/mnt/e/Games/JP/Umamusume/umamusume_Data/Persistent/meta")
    return parser.parse_args()


def clean_key(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def serialize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return list(value)
    if isinstance(value, Mapping):
        return {clean_key(k): serialize(v) for k, v in value.items()}
    if isinstance(value, Sequence):
        return [serialize(item) for item in value]
    return str(value)


def detect_kind(normalized_name: str) -> Optional[str]:
    if HOME_PATTERN.search(normalized_name):
        return "home"
    if STORY_PATTERN.search(normalized_name):
        return "story"
    if RACE_PATTERN.search(normalized_name):
        return "race"
    return None


def collect_story_fields(data: Any) -> Dict[str, Any]:
    collected: Dict[str, List[Any]] = {field: [] for field in TARGET_FIELDS}

    def traverse(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in TARGET_FIELDS:
                    collected[key].append(value)
                traverse(value)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(data)

    filtered: Dict[str, Any] = {}
    for key, values in collected.items():
        if not values:
            continue
        filtered[key] = values[0] if len(values) == 1 else values
    return filtered


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _open_encrypted_meta(meta_path: Path) -> apsw.Connection:
    connection = apsw.Connection(str(meta_path), flags=apsw.SQLITE_OPEN_READONLY)
    connection.pragma("cipher", DEFAULT_CIPHER_NAME)
    connection.pragma("hexkey", DEFAULT_DATABASE_KEY.hex())
    connection.pragma("user_version")
    return connection


def get_mono_name(mono, tree: Dict) -> Optional[str]:
    for attr in ("m_Name", "name"):
        value = getattr(mono, attr, None)
        if isinstance(value, str) and value:
            return value
    value = tree.get("m_Name")
    if isinstance(value, str) and value:
        return value
    return None


def get_script_name(mono) -> Optional[str]:
    script = getattr(mono, "m_Script", None)
    if not script:
        return None
    try:
        script_obj = script.read()
    except Exception:
        return None
    for attr in ("name", "m_Name"):
        value = getattr(script_obj, attr, None)
        if isinstance(value, str) and value:
            return value
    return None


def get_asset_path(data_dir: str, name: str) -> str:
    segments = [segment for segment in name.replace("\\", "/").split("/") if segment]
    return os.path.join(data_dir, *segments)


def extract_asset(data_dir: str, output_dir: str, source_name: str, kind: str) -> Tuple[str, str, List[str]]:
    result_path = os.path.join(output_dir, f"{source_name}.json")
    logs: List[str] = []

    asset_path = get_asset_path(data_dir, source_name)
    if not os.path.exists(asset_path):
        return "warn", f"Asset not found for {source_name}: {asset_path}", logs

    try:
        env = UnityPy.load(asset_path)
    except Exception as exc:
        return "error", f"Failed loading asset {source_name}: {exc}", logs

    entries = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            mono = obj.read()
            tree = obj.read_typetree()
        except Exception as exc:
            logs.append(f"[W] Failed reading MonoBehaviour {obj.path_id}: {exc}")
            continue

        mono_name = get_mono_name(mono, tree)
        script_name = get_script_name(mono)
        serialized = serialize(tree)
        data_payload = collect_story_fields(serialized) if kind in ("story", "home") else serialized
        entries.append(
            {
                "Name": mono_name or "",
                "Script": script_name or "",
                "PathID": obj.path_id,
                "Data": data_payload,
            }
        )

    payload = {
        "AssetPath": source_name,
        "MonoBehaviours": entries,
    }

    ensure_parent_dir(result_path)
    try:
        with open(result_path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
    except OSError as exc:
        return "error", f"Failed writing {result_path}: {exc}", logs

    return "info", f"Extracted {source_name}.json", logs


def load_text_sources(meta_path: str) -> List[Tuple[str, str]]:
    text_sources: List[Tuple[str, str]] = []
    connection = _open_encrypted_meta(Path(meta_path))
    try:
        cursor = connection.cursor()
        for (name,) in cursor.execute("SELECT n FROM a"):
            if not name:
                continue
            normalized = str(name).replace("\\", "/")
            kind = detect_kind(normalized)
            if kind:
                text_sources.append((normalized, kind))
    finally:
        connection.close()
    return text_sources


def main() -> None:
    args = parse_args()

    meta_path = args.meta_path or os.path.join(args.data_dir, "meta")
    if not os.path.exists(meta_path):
        print(f"[E] Meta database not found: {meta_path}")
        return

    try:
        text_sources = load_text_sources(meta_path)
    except apsw.Error as exc:
        print(f"[E] Failed reading meta database: {exc}")
        return

    if not text_sources:
        print("[I] No story or race assets discovered.")
        return

    workers = max(1, args.thread)

    try:
        with Progress(*PROGRESS_COLUMNS, transient=True) as progress:
            task_id = progress.add_task("Extracting", total=len(text_sources))
            with ProcessPoolExecutor(max_workers=workers) as pool:
                future_to_source = {pool.submit(extract_asset, args.data_dir, args.output_dir, source_name, kind): (source_name, kind) for source_name, kind in text_sources}

                for future in as_completed(future_to_source):
                    source_name, kind = future_to_source[future]
                    try:
                        status, message, logs = future.result()
                    except Exception as exc:
                        progress.console.log(f"[E] Unexpected failure processing {source_name}: {exc}")
                    else:
                        for line in logs:
                            progress.console.log(line)
                        if status != "info":
                            prefix = {"warn": "[W]", "error": "[E]"}.get(status, "[E]")
                            progress.console.log(f"{prefix} {message}")
                    finally:
                        progress.update(task_id, advance=1)
    except KeyboardInterrupt:
        print("[W] Extraction interrupted by user request")


if __name__ == "__main__":
    main()
