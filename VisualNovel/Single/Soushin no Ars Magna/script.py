import argparse
import json
from glob import glob

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_VN\scenario")
    p.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    p.add_argument("-ft", type=float, default=0)
    return p.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace(" ", "").replace(";", "")
    return text


def process_type0(data, results):
    for cut in data["cuts"]:
        if cut["window"] is None:
            continue
        Text = cut["window"]["texts"][0]
        Text = text_cleaning(Text)
        Speaker = cut["window"]["tag"]
        Speaker = Speaker.split(":")[-1]
        Voice = cut["audio"]["voice"]
        if Voice is None:
            continue
        Voice = Voice["file"].split("/")[-1]
        results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})


PROCESSORS = {0: process_type0}


def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.json", recursive=True)

    results = []
    for fn in tqdm(filelist, ncols=150):
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)

        processor(data, results)

        if not results:
            continue

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
