import argparse
import json
import re
from glob import glob

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("-ft", type=int, default=0)
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "").replace("　", "")

    # 1) 把真实控制字符先规范化为可见的反斜杠序列
    control_map = {"\n": "n", "\r": "r", "\t": "t", "\f": "f", "\v": "v"}
    for ch, letter in control_map.items():
        text = text.replace(ch, "\\" + letter)

    # 2) 先删除带参标记
    patterns_param = [
        r"\\f(?:\d+|\[[^\]]*\])",  # \f123 or \f[...]
        r"\\fr(?:\d+|\[[^\]]*\])",  # \fr123 or \fr[...]
        r"\\w\d+",  # \w123
        r"\\wf\d+",  # \wf123
        r"\\c0x[0-9A-Fa-f]+",  # \c0xRRGGBB
        r"\\cr0x[0-9A-Fa-f]+",
        r"\\cs0x[0-9A-Fa-f]+",
    ]
    text = re.sub("|".join(patterns_param), "", text)

    # 3) 再删除无参标记
    simple_tokens = ["fss", "fll", "fn", "fs", "fr", "fl", "pl", "pc", "pr", "c", "@", "n", "f"] # from catsystemunity
    simple_tokens = sorted(simple_tokens, key=len, reverse=True)
    for tok in simple_tokens:
        text = text.replace("\\" + tok, "")

    text = re.sub(r"[ \t\u3000]+", " ", text).strip()
    return text


def process_type0(data, results):
    items = data["items"]
    n = len(items)
    i = 0
    while i < n:
        it = items[i]
        kind = it["kind"]
        if kind == "command" and it["opcode"] == "pcm":
            # 收集连续的 pcm 语音
            voices = []
            j = i
            while j < n and items[j]["kind"] == "command" and items[j]["opcode"] == "pcm":
                voices.append(items[j]["args"][0])
                j += 1
            # 期望后面紧跟 name 与 message
            if j + 1 >= n:
                raise ValueError("pcm/name/message 三连不完整：到达末尾")
            name_item = items[j]
            msg_item = items[j + 1]
            if name_item["kind"] != "name" or msg_item["kind"] != "message":
                raise ValueError(f"pcm/name/message 三个 block 不连续: 在 index {it['index']} 后不是 name+message")
            # 单个 pcm：即便 name 含“＆”，也按单条处理；多个 pcm 则按“＆”拆分并逐一对应
            speakers_raw = name_item["name"].split("＠")[0]
            text = msg_item["text"]
            if len(voices) == 1:
                results.append({"Speaker": speakers_raw, "Voice": voices[0], "Text": text_cleaning(text)})
            else:
                speakers = [s.strip() for s in speakers_raw.split("＆") if s.strip()]
                if len(speakers) != len(voices):
                    raise ValueError(f"pcm 数量与说话人数量不匹配: voices={len(voices)}, speakers={len(speakers)} @ index {it['index']}")
                for k in range(len(voices)):
                    results.append({"Speaker": speakers[k], "Voice": voices[k], "Text": text_cleaning(text)})
            # 跳过已处理的块
            i = j + 2
            continue
        i += 1


def process_type1(data, results):
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
            processor(data, results)

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
