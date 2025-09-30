import argparse
import io
import json
import os
import pathlib
import re
from typing import Dict, List, Optional, Tuple

from parsec_envinit import parse_envinit_characters


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\\Fuck_VN\\scenario")
    parser.add_argument("-op", type=str, default=r"D:\\Fuck_VN\\index.json")
    parser.add_argument("-tjs_root", type=str, default=r"D:\\Fuck_VN\\data")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = re.sub(r"^【[^】]*】\s*", "", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("／", "")
    return text


def is_comment_or_empty(line: str) -> bool:
    ls = line.strip()
    return (not ls) or ls.startswith(";")


def load_mapping(tjs_root: str) -> Dict[str, Tuple[str, str]]:
    envinit_path = os.path.join(tjs_root, "envinit.tjs")
    try:
        with io.open(envinit_path, "r", encoding="cp932", errors="ignore") as ef:
            env_text = ef.read()
        rows = parse_envinit_characters(env_text)
    except Exception:
        rows = []
    mapping: Dict[str, Tuple[str, str]] = {}
    for char_key, voice_name, voice_file in rows:
        if char_key:
            mapping[char_key] = (voice_name, voice_file)
        if voice_name:
            mapping[voice_name] = (voice_name, voice_file)
    return mapping


def main(JA_dir: str, op_json: str, tjs_root: str):
    mapping = load_mapping(tjs_root)
    results: List[Tuple[str, str, str]] = []

    ks_dir = pathlib.Path(JA_dir)
    files = [p for p in ks_dir.rglob("*.ks") if p.is_file()]

    name_label_re = re.compile(r"^【([^】]+)】")
    tag_re = re.compile(r"^\[(.*?)\]\s*$")

    for path in files:
        with io.open(str(path), "r", encoding="cp932", errors="ignore") as f:
            lines = f.readlines()

        # Per-file: current numeric voice id per speaker
        cur_voice_num: Dict[str, Optional[int]] = {}

        i = 0
        while i < len(lines):
            raw = lines[i]
            line = raw.rstrip("\n\r;")
            stripped = line.strip()

            # [ ... ] tag line handling
            m = tag_re.match(stripped)
            if m:
                content = m.group(1)

                # Handle voice assignment: [キャラ voice=数字] or [voice name=キャラ voice=数字]
                if "voice=" in content:
                    parts = content.split()
                    params: Dict[str, str] = {}
                    speaker_hint: List[str] = []
                    for tok in parts:
                        if "=" in tok:
                            k, v = tok.split("=", 1)
                            params[k.strip().lower()] = v.strip().strip("\"'")
                        else:
                            if not params:  # only collect tokens before first key=value
                                speaker_hint.append(tok)
                    speaker: Optional[str] = None
                    if "name" in params:
                        speaker = params["name"].strip()
                    elif speaker_hint:
                        speaker = " ".join(speaker_hint).strip()
                    vnum: Optional[int] = None
                    if "voice" in params and re.fullmatch(r"\d+", params["voice"] or ""):
                        vnum = int(params["voice"]) if params["voice"] else None

                    if speaker and vnum is not None:
                        # Normalize speaker: left of '／' or '/'
                        speaker_core = re.split(r"[／/]", speaker)[0].strip()
                        key = speaker_core.split()[0] if speaker_core else speaker
                        cur_voice_num[key] = vnum
                i += 1
                continue

            # Non-tag line: if it's a dialogue line with 【Name】, emit voice then auto-increment
            if not is_comment_or_empty(line):
                mname = name_label_re.match(line)
                if mname:
                    raw_speaker = mname.group(1).strip()
                    # Normalize
                    speaker_core = re.split(r"[／/]", raw_speaker)[0].strip()
                    speaker = speaker_core.split()[0] if speaker_core else raw_speaker

                    # Resolve voice template
                    entry = mapping.get(speaker)
                    if not entry and speaker:
                        entry = mapping.get(speaker.replace(" ", ""))

                    # Only generate when we have a current numeric voice id
                    if entry and (speaker in cur_voice_num) and (cur_voice_num[speaker] is not None):
                        _, voice_file_tpl = entry
                        num = int(cur_voice_num[speaker])  # current id
                        voice_str = voice_file_tpl % (num, "")
                        voice_str = voice_str.replace(".ogg", "")
                        if voice_str:
                            text = text_cleaning(line)
                            results.append((speaker, voice_str, text))
                            # Auto-increment after use
                            cur_voice_num[speaker] = num + 1
            i += 1

    # Deduplicate by Voice
    seen = set()
    json_data = []
    for Speaker, Voice, Text in results:
        if Voice not in seen:
            seen.add(Voice)
            json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})

    with open(op_json, mode="w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, args.tjs_root)
