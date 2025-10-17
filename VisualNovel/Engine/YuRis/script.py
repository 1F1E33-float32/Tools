import argparse
import json
import re
from glob import glob
from typing import Any, Dict, List

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\ysbin")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("-ft", type=int, default=0)
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "")
    return text


def parse_word_line(raw: str):
    s = raw.strip()
    pair_patterns = [
        r"^【(?P<sp>[^】]+)】(?P<tx>.*)$",  # 【Speaker】Text
        r"^(?P<sp>[^「]+)「(?P<tx>.*)」$",  # Speaker「Text」
        r"^(?P<sp>[^『]+)『(?P<tx>.*)』$",  # Speaker『Text』
        r"^(?P<sp>[^（]+)（(?P<tx>.*)）$",  # Speaker（Text）全角
    ]

    for pat in pair_patterns:
        m = re.match(pat, s)
        if m:
            return m.group("sp").strip(), m.group("tx").strip()

    return "？？？", s


def process_type0(lines: List[Dict[str, Any]], results: List[Dict[str, Any]]):
    """
    扫描相邻的 (GOSUB -> WORD) 配对：
      - GOSUB:
          expressions[0].ast.value == "\"es.SND\""
          expressions[1].ast.value == 21
          expressions[2].ast.value -> Voice (去掉外层引号)
      - 紧随的 WORD:
          expressions[0].ast.value -> RawStringLiteral
          用正则拆为 Speaker 与 Text
      - 如果 WORD 后面是 _，继续往下找 WORD 并 append Text
    命中则追加 {Speaker, Voice, Text}
    """
    i = 0
    n = len(lines)
    while i < n:
        cur = lines[i]
        if cur["id"] == "GOSUB" and (i + 1) < n:
            if lines[i + 1]["id"] != "WORD":
                i += 1
                continue
            expressions = cur["expressions"]
            if len(expressions) >= 3:
                v1 = expressions[0]["text"]
                if v1 == '#="\\"es.SND\\""':
                    v2 = expressions[1]["text"]
                    if v2 == "PINT=21":
                        Voice = expressions[2]["ast"]["value"]
                        Voice = re.search(r'["\']([^"\']*)["\']', Voice).group(1)
                        if not Voice:
                            i += 1
                            continue

                        raw_text = ""
                        j = i + 1

                        while j < n:
                            if lines[j]["id"] == "WORD":
                                word_value = lines[j]["expressions"][0]["ast"]["value"]
                                raw_text += word_value
                                j += 1
                            elif lines[j]["id"] == "_":
                                j += 1
                            elif lines[j]["id"] == "RETURNCODE":
                                break
                            else:
                                raise Exception("Error")

                        if raw_text:
                            Speaker, Text = parse_word_line(raw_text)
                            results.append({"Speaker": Speaker, "Voice": Voice, "Text": text_cleaning(Text)})
        i += 1


def process_type1(lines: List[Dict[str, Any]], results: List[Dict[str, Any]]):
    return


PROCESSORS = {
    0: process_type0,
    1: process_type1,
}


def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.json", recursive=True)

    results = []
    for fn in tqdm(filelist, ncols=150):
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            lines = data.get("commands")
            if lines:
                processor(lines, results)

    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(op_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, args.ft)
