import argparse
import json
from glob import glob

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("-ft", type=int, default=0)
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("」", "").replace("「", "").replace("（", "").replace("）", "").replace("『", "").replace("』", "")
    text = text.replace("　", "")
    return text


def process_type0(data, results):
    instructions = data.get("instructions", [])

    i = 0
    while i < len(instructions):
        inst = instructions[i]

        # 检查是否是 callp + $user_voice@KOEKOE
        if inst.get("opcode", {}).get("mnemonic") == "callp" and inst.get("resolved_name") == "$user_voice@KOEKOE":
            # 往上找 ldstr 获取 Voice
            voice = None
            prev_inst = instructions[i - 1]
            if prev_inst["opcode"]["mnemonic"] == "ldstr":
                voice = prev_inst["string"]
                voice = voice.replace("\\", "")
                voice = voice.split(".")[0]

            # 进入target状态，扫描到proc为止
            target = True
            skip = False
            speaker = None
            text = None
            texts = []  # 收集所有text指令
            j = i + 1

            while j < len(instructions) and target:
                curr_inst = instructions[j]
                mnemonic = curr_inst.get("opcode", {}).get("mnemonic")

                # 遇到另一个 $user_voice@KOEKOE，退出当前target
                if mnemonic == "callp" and curr_inst.get("resolved_name") == "$user_voice@KOEKOE":
                    target = False
                    skip = True
                    j += 1
                    break

                # 遇到 proc，结束target
                if mnemonic == "proc":
                    target = False
                    j += 1
                    break

                # 收集 text
                if mnemonic == "text":
                    texts.append(curr_inst.get("string"))

                j += 1

            if not skip:
                if len(texts) == 1:
                    # 只有一个text，没有speaker
                    speaker = "？？？"
                    text = texts[0]
                elif len(texts) == 2:
                    # 至少两个text，第一个是speaker，第二个是text
                    speaker = texts[0]
                    text = texts[1]
                else:
                    print(voice)

                if speaker == "　":
                    speaker = "？？？"

                # 确保voice和text都不是None
                if voice is not None and text is not None:
                    cleaned = text_cleaning(text)
                    results.append({"Speaker": speaker, "Voice": voice, "Text": cleaned})

                # 跳到扫描后的位置
                i = j
                continue

        i += 1


def process_type1(data, results):
    pass


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
        with open(fn, encoding="utf-8") as fp:
            data = json.load(fp)

        processor(data, results)

        if not results:
            continue

    seen = set()
    unique_results = []
    for entry in results:
        v = entry["Voice"].lower()
        if v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(op_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, args.ft)
