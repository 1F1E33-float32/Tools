import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\\Fuck_VN\\script", help="包含脚本 JSON 的目录")
    return p.parse_args(args=args, namespace=namespace)


FEATURE_DIR = Path(__file__).parent / "feature"


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
