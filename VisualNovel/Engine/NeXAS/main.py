import argparse
import json
import os
import re
from glob import glob

from tool.disassembler import Disassembler
from tool.message import text_analyze
from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("-ft", type=float, default=1)
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "").replace("〔", "").replace("〕", "").replace("《", "").replace("》", "")
    text = text.replace("　", "")
    return text


def get_text(text):
    Voice = Text = None
    match = re.match(r"\[\d+\](.*)", text)
    if match:
        result, display = text_analyze(match.group(1))
        if result and display:
            for item in result:
                if item.escape.name == "VOICE":
                    Voice = item.command
                    Text = text_cleaning(display)

    return Voice, Text


def main(JA_dir, op_json, force_type):
    filelist = glob(f"{JA_dir}/**/*.bin", recursive=True)
    filelist += glob(f"{JA_dir}/**/*.binu8", recursive=True)

    global_bin = None
    filtered_filelist = []

    for f in filelist:
        if os.path.basename(f).lower() == "__global.bin" or os.path.basename(f).lower() == "__global.binu8":
            global_bin = f
        else:
            filtered_filelist.append(f)
    results = []
    match force_type:
        case 0:
            disassembler = Disassembler(r"VisualNovel\Engine\NeXAS\version_0.yaml")
        case 1:
            disassembler = Disassembler(r"VisualNovel\Engine\NeXAS\version_1.yaml")
        case 2:
            disassembler = Disassembler(r"VisualNovel\Engine\NeXAS\version_2.yaml")
    disassembler.load_and_disassemble_global(global_bin)
    for filename in tqdm(filtered_filelist, ncols=150):
        dis_result = disassembler.disassemble(filename)
        for label in dis_result["code"]:
            for i, block in enumerate(label["instructions"]):
                out_mnemonic = block["mnemonic"]
                out_operand = block.get("operand")
                out_param_type = block.get("param_type")
                out_comment = block.get("comment")

                if out_mnemonic and out_operand and out_param_type and out_comment:
                    if out_mnemonic == "PARAM" and out_operand == 1 and out_param_type == "@STRING":
                        Voice, Text = get_text(out_comment)
                        if Voice and Text:
                            if "@u" in Text or "@b" in Text or "@*name" in Text:
                                continue
                            if label["instructions"][i - 1]["mnemonic"] == "VAL" and label["instructions"][i - 1]["comment"] == "":
                                if label["instructions"][i - 2]["mnemonic"] == "PARAM":
                                    Speaker = label["instructions"][i - 2]["comment"]
                                    match = re.match(r"\[\d+\](.*)", Speaker)
                                    if match:
                                        Speaker = match.group(1)
                                        Speaker = Speaker.replace("　", "").replace(" ", "").replace("\t", "").replace("*", "")
                                        if Speaker == "":
                                            Speaker = "？？？"
                                        Speaker = re.sub(r"@[0-9A-Za-z_-]*", "", Speaker)
                                        results.append((Speaker, Voice, Text))

    with open(op_json, mode="w", encoding="utf-8") as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            if Voice.lower() not in seen:
                seen.add(Voice.lower())
                json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, args.ft)
