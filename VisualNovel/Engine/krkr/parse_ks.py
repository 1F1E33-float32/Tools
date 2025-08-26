import json
import chardet
import argparse
from tqdm import tqdm
from glob import glob
from parse_ks_types import (
    process_type0, process_type0_1, process_type0_2, process_type0_3,
    process_type1, process_type1_1, process_type1_2,
    process_type2,
    process_type3, process_type3_1,
    process_type4,
    process_type5,
    process_type6, process_type6_1,
    process_type7,
    process_type999,
)


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\scenario")
    p.add_argument("-op", type=str, default=r"D:\Fuck_galgame\index.json")
    p.add_argument("-ft", type=float, default=0.3)
    return p.parse_args(args=args, namespace=namespace)


def guess_encoding(path):
    with open(path, "rb") as f:
        raw = f.read()
    enc = chardet.detect(raw)["encoding"]
    return enc


def load_lines(path):
    try:
        with open(path, "r", encoding=guess_encoding(path)) as f:
            lines = f.readlines()
    except (UnicodeDecodeError, TypeError):
        with open(path, "r", encoding="cp932") as f:
            lines = f.readlines()
    return [ln.lstrip() for ln in lines if not ln.lstrip().startswith(";")]


PROCESSORS = {
    0:   process_type0,
    0.1: process_type0_1,
    0.2: process_type0_2,
    0.3: process_type0_3,
    1:   process_type1,
    1.1: process_type1_1,
    1.2: process_type1_2,
    2:   process_type2,
    3:   process_type3,
    3.1: process_type3_1,
    4:   process_type4,
    5:   process_type5,
    6:   process_type6,
    6.1: process_type6_1,
    7:   process_type7,
    999: process_type999,
}


def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.ks", recursive=True) + glob(f"{JA_dir}/**/*.ms", recursive=True) + glob(f"{JA_dir}/**/*.scn", recursive=True)

    results = []
    for fn in tqdm(filelist):
        lines = load_lines(fn)

        processor(lines, results)

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
