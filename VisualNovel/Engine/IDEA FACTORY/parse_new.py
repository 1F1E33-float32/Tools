import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from tqdm import tqdm

VOICE_FUNC_LIST = ["fn_14D7C", "fn_15274", "fn_152A4", "fn_18154"]
SPEAKER_FUNC_LIST = ["fn_105C8", "fn_105F8", "fn_12648"]
TEXT_FUNC_LIST = ["fn_11E3C", "fn_FD88", "fn_FECC", "fn_FEFC"]
COMBINE_FUNC_LIST = ["fn_33CC8", "fn_3B278"]

FUNCDEF_TYPE0 = {
    "VOICE_FUNC": VOICE_FUNC_LIST,
    "SPEAKER_FUNC": SPEAKER_FUNC_LIST,
    "TEXT_FUNC": TEXT_FUNC_LIST,
}

FUNCDEF_TYPE1 = {
    "SPEAKER_FUNC": SPEAKER_FUNC_LIST,
    "VOICE_FUNC": VOICE_FUNC_LIST,
    "TEXT_FUNC": TEXT_FUNC_LIST,
}

FUNCDEF_TYPE2 = {
    "SPEAKER_FUNC": SPEAKER_FUNC_LIST,
    "COMBINE_FUNC": COMBINE_FUNC_LIST,
}


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
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


def _is_call(inst: Dict, fn_name: Union[str, Sequence[str]]) -> bool:
    if not (isinstance(inst, dict) and inst.get("action") == "call"):
        return False
    target = inst.get("target")
    if isinstance(fn_name, (list, tuple, set)):
        return target in fn_name
    return target == fn_name


def _is_voice_block(inst: Dict, voice_func: Union[str, Sequence[str]]) -> Optional[int]:
    if not _is_call(inst, voice_func):
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


def _is_speaker_block(inst: Dict, speaker_func: Union[str, Sequence[str]]) -> Optional[Tuple[str, Optional[int]]]:
    if not _is_call(inst, speaker_func):
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


def _extract_text_from_call(inst: Dict, text_func: Union[str, Sequence[str]]) -> Optional[str]:
    if not _is_call(inst, text_func):
        return None
    for p in inst.get("params") or []:
        if isinstance(p, dict):
            s = p.get("string")
            if isinstance(s, str):
                return s
    return None


def _extract_voice_text_from_combine_call(inst: Dict, combine_funcs: Union[str, Sequence[str]]) -> Optional[Tuple[Optional[int], Optional[int], str, str]]:
    if not _is_call(inst, combine_funcs):
        return None
    params = inst.get("params") or []
    voice1: Optional[int] = None
    voice2: Optional[int] = None
    text1_parts: List[str] = []
    text2_parts: List[str] = []
    for p in params:
        if not isinstance(p, dict) or p.get("type") != "DataPointer":
            continue
        if "u32" in p:
            u = p.get("u32")
            if isinstance(u, int):
                if u > 0:
                    if voice1 is None:
                        voice1 = u
                        continue
                    if voice2 is None:
                        voice2 = u
                        continue
            continue
        s = p.get("string")
        if isinstance(s, str):
            if voice2 is not None:
                text2_parts.append(s)
            else:
                text1_parts.append(s)
    t1 = "".join(text1_parts)
    t2 = "".join(text2_parts)
    return (voice1, voice2, t1, t2)


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
    VOICE_FUNC = FUNCDEF_TYPE0["VOICE_FUNC"]
    SPEAKER_FUNC = FUNCDEF_TYPE0["SPEAKER_FUNC"]
    TEXT_FUNC = FUNCDEF_TYPE0["TEXT_FUNC"]

    def proc(insts: List[Dict], i: int):
        n = len(insts)
        if i >= n:
            return i, []
        voice_num = _is_voice_block(insts[i], VOICE_FUNC)
        if voice_num is None:
            return i, []
        voice = f"{voice_num:06d}"
        speaker = "？？？"
        speaker_id: Optional[int] = None

        j = i + 1
        if j < n:
            spk = _is_speaker_block(insts[j], SPEAKER_FUNC)
            if spk is not None:
                speaker, speaker_id = spk
                speaker = re.sub(r"\[.*?\]", "", speaker).replace(" ", "")
                j += 1

        text_parts: List[str] = []
        while j < n:
            cur = insts[j]
            if not _is_call(cur, TEXT_FUNC):
                break
            t = _extract_text_from_call(cur, TEXT_FUNC)
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
    SPEAKER_FUNC = FUNCDEF_TYPE1["SPEAKER_FUNC"]
    VOICE_FUNC = FUNCDEF_TYPE1["VOICE_FUNC"]
    TEXT_FUNC = FUNCDEF_TYPE1["TEXT_FUNC"]

    def proc(insts: List[Dict], i: int):
        n = len(insts)
        if i >= n:
            return i, []
        spk = _is_speaker_block(insts[i], SPEAKER_FUNC)
        if spk is None:
            return i, []
        j = i + 1
        if j >= n:
            return i, []
        voice_num = _is_voice_block(insts[j], VOICE_FUNC)
        if voice_num is None:
            return i, []
        voice = f"{voice_num:06d}"
        j += 1

        text_parts: List[str] = []
        while j < n:
            cur = insts[j]
            if not _is_call(cur, TEXT_FUNC):
                break
            t = _extract_text_from_call(cur, TEXT_FUNC)
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


def make_processor_type2():
    SPEAKER_FUNC = FUNCDEF_TYPE2["SPEAKER_FUNC"]
    COMBINE_FUNC = FUNCDEF_TYPE2["COMBINE_FUNC"]

    def proc(insts: List[Dict], i: int):
        n = len(insts)
        if i >= n:
            return i, []

        speaker = "？？？"
        speaker_id: Optional[int] = None
        j = i

        spk = _is_speaker_block(insts[j], SPEAKER_FUNC)
        if spk is not None:
            speaker, speaker_id = spk
            speaker = re.sub(r"\[.*?\]", "", speaker).replace(" ", "")
            j += 1

        if j >= n:
            return i, []

        comb = _extract_voice_text_from_combine_call(insts[j], COMBINE_FUNC)
        if comb is None:
            return i, []

        v1, v2, t1, t2 = comb

        # Only keep the second voice/text; ignore zeros
        if not (isinstance(v2, int) and v2 > 0):
            return i, []  # skip cases where second voice is 0 or missing

        text2 = text_cleaning(_clean_placeholder_names(t2))
        voice2 = f"{v2:06d}"

        out: List[Tuple[str, Optional[int], str, str]] = []
        if text2:
            # speaker_id unknown for this pattern per requirement -> set to -1
            out.append((speaker, -1, voice2, text2))
        return j + 1, out

    return proc


def run_with_version(JA_dir: str, op_json: str) -> None:
    proc0 = make_processor_type0()
    proc1 = make_processor_type1()
    proc2 = make_processor_type2()

    ja_path = Path(JA_dir)
    filelist = sorted(ja_path.rglob("*.json"))

    collected: List[Tuple[str, Optional[int], str, str]] = []

    for jf in tqdm(filelist, ncols=150):
        doc = json.loads(jf.read_text(encoding="utf-8"))
        for _fn_name, insts in _iter_instruction_lists(doc):
            i, n = 0, len(insts)
            while i < n:
                new_i, out = proc2(insts, i)
                if out:
                    collected.extend(out)
                    i = new_i
                    continue

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
