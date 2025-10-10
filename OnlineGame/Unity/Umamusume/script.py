import argparse
import io
import json
import os
import re
import struct
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import apsw
import numpy as np
import UnityPy
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--RAW", dest="data_dir", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/RAW")
    parser.add_argument("--EXP", dest="output_dir", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/EXP")
    parser.add_argument("--meta", dest="meta_path", default=r"/mnt/e/Games/JP/Umamusume/umamusume_Data/Persistent/meta")
    parser.add_argument("--index", dest="index_path", default=r"/mnt/e/OnlineGame_Dataset/Umamusume/index.json")
    parser.add_argument("--thread", type=int, default=os.cpu_count())
    return parser.parse_args()


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
REQUIRED_FIELDS = ("VoiceSheetId", "CueId", "CharaId", "Name", "Text")

# fmt: off
DEFAULT_DATABASE_KEY = bytes([
    0x9C, 0x2B, 0xAB, 0x97, 0xBC, 0xF8, 0xC0, 0xC4,
    0xF1, 0xA9, 0xEA, 0x78, 0x81, 0xA2, 0x13, 0xF6,
    0xC9, 0xEB, 0xF9, 0xD8, 0xD4, 0xC6, 0xA8, 0xE4,
    0x3C, 0xE5, 0xA2, 0x59, 0xBD, 0xE7, 0xE9, 0xFD,
])


DEFAULT_BUNDLE_BASE_KEYS = bytes([
    0x53, 0x2B, 0x46, 0x31, 0xE4, 0xA7, 0xB9, 0x47,
    0x3E, 0x7C, 0xFB,
])
# fmt: on
DECRYPTION_OFFSET = 256

_KEY_CACHE: Dict[Tuple[bytes, int], np.ndarray] = {}


def text_cleaning(text):
    text = text.replace("」", "").replace("「", "").replace("』", "").replace("『", "").replace("（", "").replace("）", "")
    text = text.replace("\r", "").replace("\n", "").replace("♪", "").replace("　", "")
    return text


def _normalize_asset_path(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _parse_meta_key(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        buffer = bytes(value)
        if not buffer:
            return None
        if len(buffer) == 8:
            return int.from_bytes(buffer, "little", signed=True)
        try:
            return int(buffer.decode("utf-8").strip(), 0)
        except (UnicodeDecodeError, ValueError):
            return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped, 0)
        except ValueError:
            return None
    return None


def _get_flat_keys(base_keys: bytes, key: int) -> np.ndarray:
    cache_key = (base_keys, key)
    cached = _KEY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    key_bytes = struct.pack("<q", int(key))
    base_arr = np.frombuffer(base_keys, dtype=np.uint8)
    key_arr = np.frombuffer(key_bytes, dtype=np.uint8)
    xor_result = np.bitwise_xor(base_arr[:, None], key_arr[None, :]).reshape(-1).astype(np.uint8)

    _KEY_CACHE[cache_key] = xor_result
    return xor_result


def decrypt_file_to_bytes(path: str, key: int, base_keys: bytes = DEFAULT_BUNDLE_BASE_KEYS) -> bytes:
    if not base_keys:
        raise ValueError("base_keys must not be empty")

    with open(path, "rb") as fp:
        data = fp.read()

    if len(data) <= DECRYPTION_OFFSET:
        return data

    keys = _get_flat_keys(base_keys, key)
    keys_len = len(keys)
    buffer = np.frombuffer(data, dtype=np.uint8).copy()
    payload = buffer[DECRYPTION_OFFSET:]

    if payload.size:
        indices = np.arange(DECRYPTION_OFFSET, len(buffer)) % keys_len
        payload ^= keys[indices]

    return buffer.tobytes()


def open_encrypted_meta_database(meta_path: Path) -> apsw.Connection:
    connection = apsw.Connection(str(meta_path), flags=apsw.SQLITE_OPEN_READONLY)
    connection.pragma("cipher", "chacha20")
    connection.pragma("hexkey", DEFAULT_DATABASE_KEY.hex())
    connection.pragma("user_version")
    return connection


def detect_asset_kind(normalized_name: str) -> Optional[str]:
    if HOME_PATTERN.search(normalized_name):
        return "home"
    if STORY_PATTERN.search(normalized_name):
        return "story"
    if RACE_PATTERN.search(normalized_name):
        return "race"
    return None


def load_text_sources(meta_path: str) -> List[Tuple[str, str, int]]:
    text_sources: List[Tuple[str, str, int]] = []
    connection = open_encrypted_meta_database(Path(meta_path))
    cursor = connection.cursor()

    for name, key_field in cursor.execute("SELECT n, e FROM a"):
        if not name:
            continue

        normalized = str(name).replace("\\", "/")
        asset_kind = detect_asset_kind(normalized)
        if not asset_kind:
            continue

        key_value = _parse_meta_key(key_field)
        if key_value is None:
            continue

        text_sources.append((normalized, asset_kind, key_value))

    return text_sources


def _convert_to_string_key(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def serialize_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return list(value)
    if isinstance(value, Mapping):
        return {_convert_to_string_key(k): serialize_value(v) for k, v in value.items()}
    if isinstance(value, Sequence):
        return [serialize_value(item) for item in value]
    return str(value)


def extract_fields_from_tree(tree: Any) -> Optional[Dict[str, Any]]:
    collected: Dict[str, Any] = {}

    def traverse(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in REQUIRED_FIELDS and key not in collected:
                    collected[key] = value
                traverse(value)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(tree)

    if not all(field in collected for field in REQUIRED_FIELDS):
        return None

    voice_sheet_id = collected.get("VoiceSheetId")
    cue_id = collected.get("CueId")
    chara_id = collected.get("CharaId")
    name = collected.get("Name")
    text = collected.get("Text")

    if not voice_sheet_id or not isinstance(voice_sheet_id, str) or not voice_sheet_id.strip():
        return None
    if not isinstance(cue_id, int) or cue_id < 0:
        return None
    if not isinstance(chara_id, int) or chara_id < 0:
        return None
    if not name or not isinstance(name, str) or not name.strip():
        return None
    if not text or not isinstance(text, str) or not text.strip():
        return None

    voice = f"snd_voi_story_{voice_sheet_id}_{cue_id:02d}"

    return {
        "Voice": voice,
        "CharaId": chara_id,
        "Speaker": name,
        "Text": text_cleaning(text),
    }


def get_asset_path(data_dir: str, name: str) -> str:
    segments = [segment for segment in name.replace("\\", "/").split("/") if segment]
    return os.path.join(data_dir, *segments)


def build_asset_key_lookup(data_dir: str, sources: Sequence[Tuple[str, str, int]]) -> Dict[str, int]:
    lookup: Dict[str, int] = {}
    for source_name, _, key in sources:
        asset_path = get_asset_path(data_dir, source_name)
        lookup[_normalize_asset_path(asset_path)] = key
    return lookup


def extract_asset(data_dir: str, source_name: str, kind: str, key: int) -> Tuple[str, str, List[Dict[str, Any]]]:
    if kind == "race":
        return "info", f"Skipped race asset {source_name}", []

    records: List[Dict[str, Any]] = []
    asset_path = get_asset_path(data_dir, source_name)

    if not os.path.exists(asset_path):
        return "warn", f"Asset not found: {asset_path}", []

    try:
        decrypted_bytes = decrypt_file_to_bytes(asset_path, key)
    except OSError as exc:
        return "error", f"Failed reading {asset_path}: {exc}", []
    except ValueError as exc:
        return "error", f"Failed decrypting {asset_path}: {exc}", []

    try:
        env = UnityPy.load(io.BytesIO(decrypted_bytes))
    except Exception as exc:
        return "error", f"Failed loading {source_name}: {exc}", []

    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue

        try:
            tree = obj.read_typetree()
        except Exception:
            continue

        serialized = serialize_value(tree)
        extracted = extract_fields_from_tree(serialized)
        if extracted:
            records.append(extracted)

    return "info", f"Extracted {len(records)} records from {source_name}", records


def main() -> None:
    args = parse_args()

    meta_path = args.meta_path or os.path.join(args.data_dir, "meta")
    if not os.path.exists(meta_path):
        print(f"[E] Meta database not found: {meta_path}")
        return

    text_sources = load_text_sources(meta_path)
    all_records: List[Dict[str, Any]] = []

    try:
        with Progress(*PROGRESS_COLUMNS, transient=True) as progress:
            task_id = progress.add_task("Extracting", total=len(text_sources))
            with ProcessPoolExecutor(max_workers=args.thread) as pool:
                future_to_source = {pool.submit(extract_asset, args.data_dir, source_name, kind, key): (source_name, kind) for source_name, kind, key in text_sources}

                for future in as_completed(future_to_source):
                    source_name, _ = future_to_source[future]
                    try:
                        status, message, records = future.result()
                        all_records.extend(records)
                        if status != "info":
                            prefix = {"warn": "[W]", "error": "[E]"}.get(status, "[I]")
                            progress.console.log(f"{prefix} {message}")
                    except Exception as exc:
                        progress.console.log(f"[E] Unexpected failure processing {source_name}: {exc}")
                    finally:
                        progress.update(task_id, advance=1)

        parent_dir = os.path.dirname(args.index_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        seen = set()
        deduped_records = []
        for rec in all_records:
            voice = rec["Voice"]
            if voice in seen:
                continue
            seen.add(voice)
            deduped_records.append(rec)

        with open(args.index_path, "w", encoding="utf-8") as fp:
            json.dump(deduped_records, fp, ensure_ascii=False, indent=2)

        print(f"[I] Extracted {len(deduped_records)} records to {args.index_path}")

    except KeyboardInterrupt:
        print("[W] Extraction interrupted by user request")


if __name__ == "__main__":
    main()
