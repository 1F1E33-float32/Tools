import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm


OPCODE_TYPE0 = {
    "VOICE_OPCODE": "0x462",
    "SPEAKER_OPCODE": "0x4BC",
    "TEXT_OPCODE": "0x4BA",
}

OPCODE_TYPE1 = {
    "SPEAKER_OPCODE": "0x4BC",
    "VOICE_OPCODE": "0x462",
    "TEXT_OPCODE": "0x4BA",
}


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-JA",
        type=str,
        default=r"E:\Games\Ryujinx_EX\Cendrillon palikA\romfs\CONTENTS\STORY_01\SCRIPT",
    )
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


_HONORIFICS = "ちゃん|君|くん|さん|様|先輩|先生"
_RE_NAME_TOKEN = re.compile(r"#Name\[(\d+)\]")
_RE_NAME_IN_QUOTES = [
    re.compile(r"[「『]\s*#Name\[\d+\]\s*[」『]"),
    re.compile(r"[（(]\s*#Name\[\d+\]\s*[）)]"),
    re.compile(r"['\"]\s*#Name\[\d+\]\s*['\"]"),
]
_RE_NAME_WITH_HONORIFIC = re.compile(rf"#Name\[\d+\](?:{_HONORIFICS})")


def _clean_placeholder_names(text: str) -> str:
    s = text
    # Strip color tags first: #Color[数字]
    s = re.sub(r"#Color\[\d+\]", "", s)
    for rx in _RE_NAME_IN_QUOTES:
        s = rx.sub("", s)
    s = _RE_NAME_WITH_HONORIFIC.sub("", s)
    s = _RE_NAME_TOKEN.sub("", s)

    # 标点收敛
    s = re.sub(r"[、]{2,}", "、", s)
    s = re.sub(r"[。]{2,}", "。", s)
    s = re.sub(r"、。", "。", s)
    s = re.sub(r"[！？]{3,}", lambda m: m.group(0)[0] * 2, s)
    s = re.sub(r"！！+", "！", s)
    s = re.sub(r"？？+", "？", s)

    s = s.replace("「」", "").replace("『』", "").replace("()", "").replace("（）", "")
    s = re.sub(r"^[、。！？\s]+", "", s)
    s = re.sub(r"[\s]+$", "", s)
    s = s.replace("、』", "』").replace("、」", "」")
    return s


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("？　", "？")
    return text


def _is_opcode(inst: Dict, opcode: str) -> bool:
    return isinstance(inst, dict) and inst.get("action") == "opcode" and str(inst.get("target")) == opcode


def _is_voice_block(inst: Dict, voice_opcode: str) -> Optional[int]:
    if not _is_opcode(inst, voice_opcode):
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


def _is_speaker_block(inst: Dict, speaker_opcode: str) -> Optional[Tuple[str, Optional[int]]]:
    if not _is_opcode(inst, speaker_opcode):
        return None
    params = inst.get("params") or []
    if len(params) < 1:
        return None
    p0 = params[0]
    if not isinstance(p0, dict):
        return None
    spk = p0.get("string")
    speaker_id: Optional[int] = None
    # 可选第二参：u32 = speaker_id
    if len(params) >= 2 and isinstance(params[1], dict):
        sid = params[1].get("u32")
        if isinstance(sid, int):
            speaker_id = sid
    if isinstance(spk, str):
        return (spk, speaker_id)
    return None


def _extract_text_from_opcode(inst: Dict, text_opcode: str) -> Optional[str]:
    if not _is_opcode(inst, text_opcode):
        return None
    for p in inst.get("params") or []:
        if isinstance(p, dict):
            s = p.get("string")
            if isinstance(s, str):
                return s
    return None


def _iter_instruction_lists(doc: Dict) -> List[Tuple[str, List[Dict]]]:
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


def make_processor_type0():
    VOICE_OPCODE = OPCODE_TYPE0["VOICE_OPCODE"]
    SPEAKER_OPCODE = OPCODE_TYPE0["SPEAKER_OPCODE"]
    TEXT_OPCODE = OPCODE_TYPE0["TEXT_OPCODE"]

    def proc(insts: List[Dict], i: int):
        n = len(insts)
        if i >= n:
            return i, []
        voice_num = _is_voice_block(insts[i], VOICE_OPCODE)
        if voice_num is None:
            return i, []
        voice = f"{voice_num:06d}"
        speaker = "？？？"
        speaker_id: Optional[int] = None

        j = i + 1
        if j < n:
            spk = _is_speaker_block(insts[j], SPEAKER_OPCODE)
            if spk is not None:
                speaker, speaker_id = spk
                speaker = re.sub(r"\[.*?\]", "", speaker).replace(" ", "")
                j += 1

        text_parts: List[str] = []
        while j < n:
            cur = insts[j]
            if not _is_opcode(cur, TEXT_OPCODE):
                break
            t = _extract_text_from_opcode(cur, TEXT_OPCODE)
            if t is not None:
                text_parts.append(t)
            j += 1

        text = text_cleaning(_clean_placeholder_names("".join(text_parts)))
        out: List[Tuple[str, Optional[int], str, str]] = []
        if text:
            out.append((speaker, speaker_id, voice, text))
        return j, out

    return proc


def make_processor_type1():
    SPEAKER_OPCODE = OPCODE_TYPE1["SPEAKER_OPCODE"]
    VOICE_OPCODE = OPCODE_TYPE1["VOICE_OPCODE"]
    TEXT_OPCODE = OPCODE_TYPE1["TEXT_OPCODE"]

    def proc(insts: List[Dict], i: int):
        n = len(insts)
        if i >= n:
            return i, []
        spk = _is_speaker_block(insts[i], SPEAKER_OPCODE)
        if spk is None:
            return i, []
        j = i + 1
        if j >= n:
            return i, []
        voice_num = _is_voice_block(insts[j], VOICE_OPCODE)
        if voice_num is None:
            return i, []
        voice = f"{voice_num:06d}"
        j += 1

        text_parts: List[str] = []
        while j < n:
            cur = insts[j]
            if not _is_opcode(cur, TEXT_OPCODE):
                break
            t = _extract_text_from_opcode(cur, TEXT_OPCODE)
            if t is not None:
                text_parts.append(t)
            j += 1

        speaker, speaker_id = spk
        speaker = re.sub(r"\[.*?\]", "", speaker).replace(" ", "")
        text = text_cleaning(_clean_placeholder_names("".join(text_parts)))
        out: List[Tuple[str, Optional[int], str, str]] = []
        if text:
            out.append((speaker, speaker_id, voice, text))
        return j, out

    return proc


def run_with_version(JA_dir: str, op_json: str) -> None:
    proc0 = make_processor_type0()
    proc1 = make_processor_type1()

    ja_path = Path(JA_dir)
    filelist = sorted(ja_path.rglob("*.json"))

    collected: List[Tuple[str, Optional[int], str, str]] = []

    for jf in tqdm(filelist, ncols=150):
        doc = json.loads(jf.read_text(encoding="utf-8"))
        for _fn_name, insts in _iter_instruction_lists(doc):
            i, n = 0, len(insts)
            while i < n:
                new_i, out = proc0(insts, i)
                if out:
                    collected.extend(out)
                    i = new_i
                    continue

                new_i, out = proc1(insts, i)
                if out:
                    collected.extend(out)
                    i = new_i
                    continue

                # 都不匹配则推进一位
                i += 1

    # speaker_id -> name 映射（填补 ？？？）
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

    # 按 Voice 去重（保留首个）
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
    a = parse_args()
    run_with_version(a.JA, a.op)
