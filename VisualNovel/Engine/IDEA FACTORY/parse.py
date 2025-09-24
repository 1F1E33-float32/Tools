import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"E:\Games\Ryujinx_EX\AMNESIA World for Nintendo Switch\romfs\CONTENTS\STORY\SCRIPT")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("--voice-func", type=str, default=r"fn_169F0")
    parser.add_argument("--speaker-func", type=str, default=r"fn_4EEAC")
    parser.add_argument("--text-func", type=str, default=r"fn_4DDE0")
    return parser.parse_args(args=args, namespace=namespace)


_HONORIFICS = "ちゃん|君|くん|さん|様|先輩|先生"

_RE_NAME_TOKEN = re.compile(r"#Name\[(\d+)\]")
_RE_NAME_IN_QUOTES = [
    re.compile(r"[「『]\s*#Name\[\d+\]\s*[」』]"),
    re.compile(r"[（(]\s*#Name\[\d+\]\s*[）)]"),
    re.compile(r"['\"]\s*#Name\[\d+\]\s*['\"]"),
]
_RE_NAME_WITH_HONORIFIC = re.compile(rf"#Name\[\d+\](?:{_HONORIFICS})")


def _clean_placeholder_names(text: str) -> str:
    s = text

    # 1) Remove quoted name tokens entirely (including the quotes)
    for rx in _RE_NAME_IN_QUOTES:
        s = rx.sub("", s)

    # 2) Remove name tokens with immediate honorific suffix
    s = _RE_NAME_WITH_HONORIFIC.sub("", s)

    # 3) Remove bare name tokens
    s = _RE_NAME_TOKEN.sub("", s)

    # 4) Punctuation cleanup
    # Collapse duplicated punctuation
    s = re.sub(r"[、]{2,}", "、", s)
    s = re.sub(r"[。]{2,}", "。", s)
    s = re.sub(r"、。", "。", s)
    s = re.sub(r"[！？]{3,}", lambda m: m.group(0)[0] * 2, s)  # cap at double
    s = re.sub(r"！！+", "！", s)
    s = re.sub(r"？？+", "？", s)

    # Remove empty quote pairs created by deletions
    s = s.replace("「」", "").replace("『』", "").replace("()", "").replace("（）", "")

    # Trim punctuation at start/end
    s = re.sub(r"^[、。！？\s]+", "", s)
    s = re.sub(r"[\s]+$", "", s)

    # Fix cases like '、』' or '、」' -> '』' / '」'
    s = s.replace("、』", "』").replace("、」", "」")

    return s


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("？　", "？")
    return text


def _is_voice_block(inst: Dict, voice_func: str) -> Optional[int]:
    # Match: action==call and params: [ DataPointer u32=NUM, DataPointer u32=0 ]
    if inst.get("action") != "call" or inst.get("target") != voice_func:
        return None
    params = inst.get("params") or []
    if len(params) < 2:
        return None
    p0, p1 = params[0], params[1]
    if not (isinstance(p0, dict) and isinstance(p1, dict)):
        return None
    if p0.get("type") != "DataPointer" or p1.get("type") != "DataPointer":
        return None
    u0 = p0.get("u32")
    u1 = p1.get("u32")
    if isinstance(u0, int) and isinstance(u1, int) and u1 == 0:
        return u0
    return None


def _is_speaker_block(inst: Dict, speaker_func: str) -> Optional[Tuple[str, Optional[int]]]:
    # Match: action==call and target==speaker_func, first param contains speaker string
    if inst.get("action") != "call" or inst.get("target") != speaker_func:
        return None
    params = inst.get("params") or []
    if len(params) < 1:
        return None
    p0 = params[0]
    if not isinstance(p0, dict):
        return None
    spk = p0.get("string")
    speaker_id: Optional[int] = None
    if len(params) >= 2 and isinstance(params[1], dict):
        sid = params[1].get("u32")
        if isinstance(sid, int):
            speaker_id = sid
    if isinstance(spk, str):
        return (spk, speaker_id)
    return None


def _extract_text_from_call(inst: Dict, text_func: str) -> Optional[str]:
    # For call instructions, find first DataPointer with string
    if inst.get("action") != "call" or inst.get("target") != text_func:
        return None
    for p in inst.get("params") or []:
        if isinstance(p, dict):
            s = p.get("string")
            if isinstance(s, str):
                return s
    return None


def _iter_instruction_lists(doc: Dict) -> List[Tuple[str, List[Dict]]]:
    """Return list of (function_name, instruction_list) for debugging.

    - New hierarchical JSON: { code_start: { fn_name: [ insts... ] } }
      -> returns [(fn_name, insts), ...]
    - Legacy flat JSON: { actions: [ insts... ] }
      -> returns [("<flat>", actions)]
    """
    pairs: List[Tuple[str, List[Dict]]] = []
    code = doc.get("code_start")
    if isinstance(code, dict):
        for fn_name, insts in code.items():
            if isinstance(insts, list):
                pairs.append((str(fn_name), insts))
        return pairs
    acts = doc.get("actions")
    if isinstance(acts, list):
        pairs.append(("<flat>", acts))
    return pairs


def main(JA_dir: str, op_json: str, *, voice_func: str, speaker_func: str, text_func: str) -> None:
    ja_path = Path(JA_dir)
    filelist = sorted(ja_path.rglob("*.json"))
    # First pass: collect raw tuples (speaker_name_or_placeholder, speaker_id, voice, text)
    collected: List[Tuple[str, Optional[int], str, str]] = []

    for jf in filelist:
        doc = json.loads(jf.read_text(encoding="utf-8"))

        for _fn_name, insts in _iter_instruction_lists(doc):
            i = 0
            n = len(insts)
            while i < n:
                inst = insts[i]
                voice_num = _is_voice_block(inst, voice_func)
                if voice_num is None:
                    i += 1
                    continue

                voice = f"{voice_num:07d}"
                speaker = "？？？"
                speaker_id: Optional[int] = None

                j = i + 1
                # optional speaker block immediately after voice
                if j < n:
                    spk = _is_speaker_block(insts[j], speaker_func)
                    if spk is not None:
                        speaker, speaker_id = spk
                        j += 1
                # Accumulate consecutive TEXT_FUNC calls; stop when function changes
                text_parts: List[str] = []
                while j < n:
                    cur = insts[j]
                    if not (isinstance(cur, dict) and cur.get("action") == "call" and cur.get("target") == text_func):
                        break
                    t = _extract_text_from_call(cur, text_func)
                    if t is not None:
                        text_parts.append(t)
                    j += 1

                text = "".join(text_parts)
                text = _clean_placeholder_names(text)
                text = text_cleaning(text)
                if text:
                    collected.append((speaker, speaker_id, voice, text))

                print(f"[block] {jf.name}, {_fn_name}, {i} -> {j - 1} voice={voice} speaker_id={speaker_id} speaker={speaker!r} text_len={len(text)}")
                i = j

    # Second pass: build speaker_id -> name mapping from known entries, then fill unknowns
    replace_dict: Dict[int, str] = {}
    for spk, sid, _voice, _text in collected:
        if sid is not None and spk != "？？？" and sid not in replace_dict:
            replace_dict[sid] = spk

    fixed_rows: List[Dict[str, str]] = []
    for spk, sid, voice, text in collected:
        name = spk
        if spk == "？？？" and sid is not None and sid in replace_dict:
            name = replace_dict[sid]
        fixed_rows.append({"Speaker": name, "Voice": voice, "Text": text})

    # Deduplicate by Voice (keep first occurrence)
    seen_voice = set()
    dedup_rows: List[Dict[str, str]] = []
    for row in fixed_rows:
        v = row.get("Voice")
        if v in seen_voice:
            continue
        seen_voice.add(v)
        dedup_rows.append(row)

    Path(op_json).parent.mkdir(parents=True, exist_ok=True)
    with open(op_json, "w", encoding="utf-8") as f:
        json.dump(dedup_rows, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, voice_func=args.voice_func, speaker_func=args.speaker_func, text_func=args.text_func)
