import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", default=r"D:\Fuck_VN\script")
    parser.add_argument("-feature", default=r"Kurenai no Homura Sanada Ninpou Chou for Nintendo Switch")
    return parser.parse_args()


def param_like(a: Any, b: Any) -> bool:
    if isinstance(b, dict):
        b_type = b.get("type")
        # Wildcard matching
        if b_type == "WildcardValue":
            return isinstance(a, dict) and a.get("type") == "Value"
        if b_type == "WildcardDataPointer":
            return isinstance(a, dict) and a.get("type") == "DataPointer"
        if b_type == "ActionRef":
            return isinstance(a, dict) and a.get("type") == "ActionRef"
        # Deep dict comparison
        if not isinstance(a, dict):
            return False
        return all(k in a and param_like(a[k], v) for k, v in b.items())
    if isinstance(b, list):
        return isinstance(a, list) and len(a) == len(b) and all(param_like(aa, bb) for aa, bb in zip(a, b))
    return a == b


def inst_matches(inst_or_insts, pat_or_start, pat_or_pattern, doc, fn_map, pattern_set) -> bool:
    if isinstance(inst_or_insts, list):
        insts = inst_or_insts
        start = pat_or_start
        pattern = pat_or_pattern
        if start + len(pattern) > len(insts):
            return False
        for i, pat in enumerate(pattern):
            if not inst_matches(insts[start + i], pat, None, doc, fn_map, pattern_set):
                return False
        return True

    # 单条指令匹配模式
    inst = inst_or_insts
    pat = pat_or_start
    act, pact = inst.get("action"), pat.get("action")
    if act != pact:
        return False
    if pact == "return":
        return True
    if pact == "opcode":
        return inst.get("target") == pat.get("target") and param_like(inst.get("params"), pat.get("params"))
    if pact == "call":
        if not param_like(inst.get("params"), pat.get("params")):
            return False
        pt = pat.get("target")
        if isinstance(pt, str) and pt.startswith("<") and pt.endswith(">"):
            sub_name = pt[1:-1]
            if sub_name == "func":
                return True
            sub_seq = pattern_set.get(sub_name)
            if not sub_seq:
                return False
            callee = inst.get("target")
            callee_insts = fn_map.get(callee) if isinstance(callee, str) else None
            if not isinstance(callee_insts, list):
                return False
            # 这里原来调用 matches_at，改为调用合并后的 inst_matches（序列分支）
            return inst_matches(callee_insts, 0, sub_seq, doc, fn_map, pattern_set)
        return True
    return False


def parse_number(token: str, *, prefer_hex: bool = False) -> int:
    t = token.strip()
    if not t:
        raise ValueError("empty number token")
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    # Determine base
    if t.lower().startswith("0x"):
        base, t = 16, t[2:]
    elif prefer_hex:
        base = 16
    elif re.fullmatch(r"[0-9A-Fa-f]+", t) and (re.search(r"[A-Fa-f]", t) or len(t) >= 8):
        base = 16
    else:
        base = 10
    val = int(t, base)
    return -val if neg else val


def parse_params(param_str: str):
    if not param_str:
        return []
    out = []
    for part in (p.strip() for p in param_str.split(",")):
        if not part or part.startswith("#"):
            break
        # Wildcards
        if part.upper() == "N":
            out.append({"type": "WildcardValue"})
        elif part.upper() == "=N":
            out.append({"type": "WildcardDataPointer"})
        elif part.startswith("[") and part.endswith("]"):
            out.append({"type": "ActionRef"})
        elif (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
            out.append({"type": "DataPointer", "string": part[1:-1]})
        elif part.startswith("="):
            out.append({"type": "DataPointer", "u32": parse_number(part[1:]), "u32_type": 0})
        else:
            out.append({"type": "Value", "value": parse_number(part)})
    return out


LABEL_RE = re.compile(r"^\s*([A-Za-z0-9_<>.-]+):\s*$")


def parse_feature_txt(text: str):
    patterns = {}
    current_name = None

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("//", "#", ";")):
            continue

        # Label detection
        m = LABEL_RE.match(line)
        if m:
            current_name = m.group(1)
            continue

        if current_name is None:
            current_name = "pattern"

        if current_name not in patterns:
            patterns[current_name] = []
        insts = patterns[current_name]
        low = line.lower()

        # Parse instructions
        if low.startswith("return"):
            insts.append({"action": "return"})
        elif low.startswith("raw "):
            body = line[4:].strip()
            if not body:
                raise ValueError("raw requires an opcode")
            op_str, _, rest = body.partition(",")
            insts.append({
                "action": "opcode",
                "target": parse_number(op_str.strip(), prefer_hex=True),
                "params": parse_params(rest) if rest else [],
            })
        elif low.startswith("call "):
            body = line[5:].strip()
            target, params_str = None, body
            if body.startswith("<"):
                end = body.find(">")
                if end != -1:
                    target = f"<{body[1:end].strip()}>"
                    params_str = body[end + 1 :].lstrip(",").lstrip()
            inst: Dict[str, Any] = {"action": "call", "params": parse_params(params_str)}
            if target:
                inst["target"] = target
            insts.append(inst)

    # Ensure 'pattern' exists
    if "pattern" not in patterns and patterns:
        patterns["pattern"] = patterns[next(iter(patterns.keys()))]

    return patterns


def find_matches_in_file(path: Path, pattern_set):
    head = pattern_set.get("pattern")
    if not head:
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))

    # inlined build_fn_map
    fn_map: Dict[str, List[Dict[str, Any]]] = {}
    code = doc.get("code_start")
    if isinstance(code, dict):
        fn_map.update({str(k): v for k, v in code.items() if isinstance(v, list)})
    acts = doc.get("actions")
    if isinstance(acts, list):
        fn_map["<flat>"] = acts

    results = []
    for fn_name, insts in fn_map.items():
        if inst_matches(insts, 0, head, doc, fn_map, pattern_set):
            results.append((fn_name, 0))
    return results


def load_all_features(category: str, feature_dir: Path):
    features = []
    index = 0
    while True:
        txt_path = feature_dir / f"{category}{index}.txt"
        if not txt_path.exists():
            break
        try:
            patset = parse_feature_txt(txt_path.read_text(encoding="utf-8"))
        except Exception:
            patset = {}
        if not patset:
            break
        features.append(patset)
        index += 1
    return features


def main(JA_dir: str, feature_name: str):
    ja_path = Path(JA_dir)
    feature_dir = Path(__file__).parent / "feature" / feature_name
    files = sorted(ja_path.rglob("*.json"))
    categories = ["VOICE", "SPEAKER", "TEXT", "COMBINE"]

    patterns_map = {cat: load_all_features(cat, feature_dir) for cat in categories}
    found = {cat: set() for cat in categories}

    for f in tqdm(files, ncols=150):
        for kind, patset_list in patterns_map.items():
            for patset in patset_list:
                for fn_name, _ in find_matches_in_file(f, patset):
                    found[kind].add(fn_name)

    for cat in categories:
        names = sorted(found[cat])
        inner = ", ".join(f'"{n}"' for n in names)
        print(f"{cat}_FUNC_LIST = [{inner}]")


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.feature)
