import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\\Fuck_VN\\script")
    return p.parse_args(args=args, namespace=namespace)


FEATURE_DIR = Path(__file__).parent / "feature" / "真紅の焔 真田忍法帳 for Nintendo Switch"


def _iter_instruction_lists(doc: Dict[str, Any]) -> Iterable[Tuple[str, List[Dict[str, Any]]]]:
    code = doc.get("code_start")
    if isinstance(code, dict):
        for fn_name, insts in code.items():
            if isinstance(insts, list):
                yield str(fn_name), insts
        return
    acts = doc.get("actions")
    if isinstance(acts, list):
        yield "<flat>", acts


def _param_like(a: Any, b: Any) -> bool:
    # Deep comparison with special handling for ActionRef
    if isinstance(b, dict):
        # Wildcard parameter in pattern matches anything
        if b.get("type") == "Any":
            return True
        # If pattern says ActionRef, only require candidate to be ActionRef (ignore addr)
        if b.get("type") == "ActionRef":
            return isinstance(a, dict) and a.get("type") == "ActionRef"
        if not isinstance(a, dict):
            return False
        for k, vb in b.items():
            if k not in a:
                return False
            if not _param_like(a[k], vb):
                return False
        return True
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            return False
        return all(_param_like(aa, bb) for aa, bb in zip(a, b))
    return a == b


def _inst_matches(inst: Dict[str, Any], pat: Dict[str, Any], doc: Dict[str, Any], fn_map: Dict[str, List[Dict[str, Any]]], pattern_set: Dict[str, List[Dict[str, Any]]]) -> bool:
    act = inst.get("action")
    pact = pat.get("action")
    if act != pact:
        return False
    if pact == "return":
        return True
    if pact == "opcode":
        # target and params must match exactly
        if inst.get("target") != pat.get("target"):
            return False
        return _param_like(inst.get("params"), pat.get("params"))
    if pact == "call":
        # params must match
        if not _param_like(inst.get("params"), pat.get("params")):
            return False
        # optional nested pattern reference via target like "<pattern1>"
        pt = pat.get("target")
        if isinstance(pt, str) and pt.startswith("<") and pt.endswith(">"):
            # Special wildcard: <all> means accept any call target without nesting
            if pt == "<all>":
                return True
            sub_name = pt[1:-1]
            sub_seq = pattern_set.get(sub_name)
            if not sub_seq:
                return False
            callee = inst.get("target")
            if not isinstance(callee, str):
                return False
            callee_insts = fn_map.get(callee)
            if not isinstance(callee_insts, list):
                return False
            return _matches_at(callee_insts, 0, sub_seq, doc, fn_map, pattern_set)
        # otherwise ignore target differences
        return True
    return False


def _matches_at(insts: List[Dict[str, Any]], start: int, pattern: List[Dict[str, Any]], doc: Dict[str, Any], fn_map: Dict[str, List[Dict[str, Any]]], pattern_set: Dict[str, List[Dict[str, Any]]]) -> bool:
    if start + len(pattern) > len(insts):
        return False
    for offset, pat in enumerate(pattern):
        if not _inst_matches(insts[start + offset], pat, doc, fn_map, pattern_set):
            return False
    return True


def _load_feature_set(name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load feature patterns from .txt (preferred) or .json.

    .txt format is a lightweight DSL, e.g.:

        pattern:
            call <all>, FFFFFF00
            return

            raw 11, =0, =1
            raw 11, =0, =1
            call <pattern1>, FFFFFF00
            return

        pattern1:
            raw 226, =101, 80000000, FFFFFF00, =0, =0, =0, =0, =0
            return
    """

    txt_path = FEATURE_DIR / f"{name}.txt"
    if txt_path.exists():
        try:
            text = txt_path.read_text(encoding="utf-8")
            patterns = _parse_feature_txt(text)
            return patterns
        except Exception:
            # Fall through to JSON if TXT parsing fails
            pass

    p = FEATURE_DIR / f"{name}.json"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        # New format: {"pattern": [...], "pattern1": [...], ...}
        if isinstance(obj, dict) and any(isinstance(v, list) for v in obj.values()):
            return {k: v for k, v in obj.items() if isinstance(v, list)}
        # Legacy format: {"patterns": [[...], ...]}
        pats = obj.get("patterns") if isinstance(obj, dict) else None
        if isinstance(pats, list) and pats:
            first = pats[0]
            if isinstance(first, list):
                return {"pattern": first}
        return {}
    except Exception:
        return {}


# ----------------------- TXT feature DSL parser -----------------------

_LABEL_RE = re.compile(r"^\s*([A-Za-z0-9_<>.-]+):\s*$")


def _parse_number(token: str, *, prefer_hex: bool = False) -> int:
    t = token.strip()
    if not t:
        raise ValueError("empty number token")
    neg = False
    if t.startswith("-"):
        neg = True
        t = t[1:]
    base = 10
    if t.lower().startswith("0x"):
        base = 16
        t = t[2:]
    elif prefer_hex:
        # For opcode values (raw ...), prefer hex (e.g., 11 -> 0x11)
        base = 16
    else:
        # Heuristics for hex-looking constants like FFFFFF00 or 80000000
        if re.fullmatch(r"[0-9A-Fa-f]+", t):
            if re.search(r"[A-Fa-f]", t) is not None:
                base = 16
            elif len(t) >= 8:  # e.g., 80000000 -> 0x80000000
                base = 16
    val = int(t, base)
    return -val if neg else val


def _make_value_param(val: int) -> Dict[str, Any]:
    return {"type": "Value", "value": val}


def _make_dp_param(val: int) -> Dict[str, Any]:
    return {"type": "DataPointer", "u32": val, "u32_type": 0}


def _parse_params(param_str: str) -> List[Dict[str, Any]]:
    if not param_str:
        return []
    parts = [p.strip() for p in param_str.split(",")]
    out: List[Dict[str, Any]] = []
    for part in parts:
        if not part:
            continue
        # Allow inline comments after params using '#'
        if part.startswith("#"):
            break
        # Wildcard parameter
        if part.lower() == "<all>" or part.lower() == "<any>":
            out.append({"type": "Any"})
            continue
        # Explicit ActionRef (ignore label/addr in pattern)
        if part.startswith("[") and part.endswith("]"):
            out.append({"type": "ActionRef"})
            continue
        # Quoted string -> DataPointer string
        if (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
            out.append({"type": "DataPointer", "string": part[1:-1]})
            continue
        if part.startswith("="):
            n = _parse_number(part[1:], prefer_hex=False)
            out.append(_make_dp_param(n))
        else:
            n = _parse_number(part, prefer_hex=False)
            out.append(_make_value_param(n))
    return out


def _parse_feature_txt(text: str) -> Dict[str, List[Dict[str, Any]]]:
    patterns: Dict[str, List[Dict[str, Any]]] = {}
    current_name: Optional[str] = None

    def ensure_current(name: str) -> List[Dict[str, Any]]:
        if name not in patterns:
            patterns[name] = []
        return patterns[name]

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Strip inline comments starting with '//' or '#'
        if line.startswith("//") or line.startswith("#") or line.startswith(";"):
            continue
        # Label
        m = _LABEL_RE.match(line)
        if m:
            current_name = m.group(1)
            continue
        if current_name is None:
            # Default to 'pattern' if no label yet
            current_name = "pattern"

        insts = ensure_current(current_name)
        low = line.lower()

        if low.startswith("return"):
            insts.append({"action": "return"})
            continue

        if low.startswith("raw "):
            # raw <opcode>, [params]
            body = line[4:].strip()
            if not body:
                raise ValueError("raw requires an opcode")
            if "," in body:
                op_str, rest = body.split(",", 1)
                op_str = op_str.strip()
                params = _parse_params(rest)
            else:
                op_str = body
                params = []
            opcode = _parse_number(op_str, prefer_hex=True)
            insts.append({
                "action": "opcode",
                "target": f"0x{opcode:X}",
                "params": params,
            })
            continue

        if low.startswith("call "):
            body = line[5:].strip()
            target: Optional[str] = None
            params_str = ""
            # Optional target like <all> or <pattern1>
            if body.startswith("<"):
                # find closing '>' then optional comma
                end = body.find(">")
                if end != -1:
                    tname = body[1:end].strip()
                    if tname.lower() == "all":
                        # wildcard: omit target (or keep as <all>)
                        target = None
                    else:
                        target = f"<{tname}>"
                    params_str = body[end+1:].lstrip()
                    if params_str.startswith(","):
                        params_str = params_str[1:].lstrip()
                else:
                    # No closing '>', treat whole body as params
                    params_str = body
            else:
                params_str = body
            params = _parse_params(params_str)
            inst: Dict[str, Any] = {"action": "call", "params": params}
            if target:
                inst["target"] = target
            insts.append(inst)
            continue

        # Unknown line, ignore gracefully
        # You can add more keywords here as needed
        continue

    # If no explicit 'pattern' but there is exactly one pattern, alias it
    if "pattern" not in patterns and patterns:
        first_name = next(iter(patterns.keys()))
        if first_name != "pattern":
            patterns["pattern"] = patterns[first_name]

    return patterns


def _build_fn_map(doc: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    fn_map: Dict[str, List[Dict[str, Any]]] = {}
    code = doc.get("code_start")
    if isinstance(code, dict):
        for k, v in code.items():
            if isinstance(v, list):
                fn_map[str(k)] = v
    acts = doc.get("actions")
    if isinstance(acts, list):
        fn_map["<flat>"] = acts
    return fn_map


def find_matches_in_file(path: Path, pattern_set: Dict[str, List[Dict[str, Any]]]) -> List[Tuple[str, int]]:
    results: List[Tuple[str, int]] = []
    if not pattern_set:
        return results
    head = pattern_set.get("pattern")
    if not head:
        return results
    doc = json.loads(path.read_text(encoding="utf-8"))
    fn_map = _build_fn_map(doc)
    for fn_name, insts in _iter_instruction_lists(doc):
        if _matches_at(insts, 0, head, doc, fn_map, pattern_set):
            results.append((fn_name, 0))
    return results


def main(JA_dir: str) -> None:
    ja_path = Path(JA_dir)
    files = sorted(ja_path.rglob("*.json"))

    patterns_map: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        "VOICE": _load_feature_set("VOICE"),
        "SPEAKER": _load_feature_set("SPEAKER"),
        "TEXT": _load_feature_set("TEXT"),
        "COMBINE": _load_feature_set("COMBINE"),
    }

    found: Dict[str, Set[str]] = {"VOICE": set(), "SPEAKER": set(), "TEXT": set(), "COMBINE": set()}

    for f in files:
        for kind, patset in patterns_map.items():
            if not patset:
                continue
            ms = find_matches_in_file(f, patset)
            for fn_name, _ in ms:
                found[kind].add(fn_name)

    def fmt_list(var: str, names: Iterable[str]) -> str:
        arr = sorted(set(str(n) for n in names))
        inner = ", ".join(f'"{x}"' for x in arr)
        return f"{var} = [{inner}]"

    print(fmt_list("VOICE_FUNC_LIST", found["VOICE"]))
    print(fmt_list("SPEAKER_FUNC_LIST", found["SPEAKER"]))
    print(fmt_list("TEXT_FUNC_LIST", found["TEXT"]))
    print(fmt_list("COMBINE_FUNC_LIST", found["COMBINE"]))


if __name__ == "__main__":
    a = parse_args()
    main(a.JA)
