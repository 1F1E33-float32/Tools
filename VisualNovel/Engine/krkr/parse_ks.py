import json
import chardet
import argparse
from tqdm import tqdm
from glob import glob
from parse_ks_types import (
    process_type0_0,
    process_type0_1,
    process_type0_2,
    process_type0_3,
    process_type0_4,
    process_type0_5,
    process_type1_0,
    process_type1_1,
    process_type1_2,
    process_type2_0,
    process_type2_1,
    process_type3_0,
    process_type3_1,
    process_type4_0,
    process_type5_0,
    process_type6_0,
    process_type6_1,
    process_type7_0,
    process_type999,
)


def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_VN\scenario")
    p.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    p.add_argument("-ft", type=float, default=1.0)
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
    0.0: process_type0_0,
    0.1: process_type0_1,
    0.2: process_type0_2,
    0.3: process_type0_3,
    0.4: process_type0_4,
    0.5: process_type0_5,
    1.0: process_type1_0,
    1.1: process_type1_1,
    1.2: process_type1_2,
    2.0: process_type2_0,
    2.1: process_type2_1,
    3.0: process_type3_0,
    3.1: process_type3_1,
    4.0: process_type4_0,
    5.0: process_type5_0,
    6.0: process_type6_0,
    6.1: process_type6_1,
    7.0: process_type7_0,
    999: process_type999,
}


def main(JA_dir, op_json, force_version):
    if force_version not in PROCESSORS:
        raise ValueError(f"未支持的解析类型: {force_version}")
    processor = PROCESSORS[force_version]

    filelist = glob(f"{JA_dir}/**/*.ks", recursive=True) + glob(f"{JA_dir}/**/*.ms", recursive=True) + glob(f"{JA_dir}/**/*.scn", recursive=True) + glob(f"{JA_dir}/**/*.txt", recursive=True)

    results = []
    for fn in tqdm(filelist, ncols=150):
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
