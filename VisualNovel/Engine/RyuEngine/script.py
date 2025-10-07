import argparse
import json
import re
from pathlib import Path


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--in_dir", default=r"D:\Fuck_VN\TextAsset")
    p.add_argument("--out_json", default=r"D:\Fuck_VN\index.json")
    return p.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "")
    return text


def remove_comments(text: str) -> str:
    text = re.sub(r"/;.*?;/", "", text, flags=re.DOTALL)
    text = re.sub(r"(?m)^[ \t]*//.*?$", "", text)
    return text


def main(text: str):
    text = remove_comments(text)
    results = []

    pat = re.compile(
        r"Message_CL\("
        r"(?P<header>.*?)"
        r"\[\#(?P<body>.*?)\#\]"
        r"\s*\)",
        re.DOTALL,
    )

    param_pat = re.compile(r'^\s*(?P<p1>\S+)\s+(?P<p2>"[^"]+"|\S+)\s+(?P<p3>\S+)\s*$', re.DOTALL)

    def norm_param(s: str | None):
        if s is None:
            return None
        s = s.strip()
        if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
            s = s[1:-1]
        return None if s.lower() == "null" else s

    for m in pat.finditer(text):
        header = m.group("header").strip()
        body = m.group("body")

        pm = param_pat.match(header)
        if not pm:
            continue
        voice = norm_param(pm.group("p2"))

        body_norm = body.replace("\r\n", "\n").replace("\r", "\n")
        lines = [ln.strip() for ln in body_norm.strip().split("\n") if ln.strip() != ""]

        if not lines:
            continue

        speaker = None if lines[0].lower() == "null" else lines[0]
        text_content = "".join(lines[1:])
        text_content = text_cleaning(text_content)

        if speaker is not None and voice is not None and text_content is not None:
            results.append({"Speaker": speaker, "Voice": voice, "Text": text_content})

    return results


if __name__ == "__main__":
    ns = parse_args()

    in_dir = Path(ns.in_dir)
    op_json = Path(ns.out_json)
    op_json.parent.mkdir(parents=True, exist_ok=True)

    results = []

    txt_files = [p for p in in_dir.glob("*.txt") if p.is_file()]

    for txt in txt_files:
        with open(txt, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        results.extend(main(content))

    seen = set()
    json_data = []
    for item in results:
        v = item.get("Voice")
        if v not in seen:
            seen.add(v)
            json_data.append(item)

    with open(op_json, mode="w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)
