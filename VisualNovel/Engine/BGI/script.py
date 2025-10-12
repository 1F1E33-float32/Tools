import argparse
import json
from glob import glob

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("-ft", type=int, default=1)
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("」", "").replace("「", "").replace("（", "").replace("）", "").replace("『", "").replace("』", "")
    text = text.replace("　", "")
    return text


def process_type0(data, results):
    '''
    line("tos19080.bss", 727);
	push_string("tos091903980"); <== Voice
	push_offset(Voice);
	call();
	f_07e(L1867b);

	line("tos19080.bss", 728);
	push_dword(1);
	push_dword(1);
	push_dword(0);
	push_string("芹沢"); <== Speaker
	push_string("「もちろん、気持ちいいですか？　って意味ですよ」"); <== Text
	msg_::f_140();
	f_07e(L1867b);
    '''
    labels = data.get("labels", {})

    for label_name, instructions in labels.items():
        in_target_block = False
        voice = None

        i = 0
        while i < len(instructions):
            inst = instructions[i]

            if inst["instruction"] == "push_string" and i + 2 < len(instructions) and instructions[i + 1]["instruction"] == "push_offset" and instructions[i + 1]["args"] and instructions[i + 1]["args"][0] == "Voice" and instructions[i + 2]["instruction"] == "call":
                voice = inst["args"][0]
                in_target_block = True
                i += 3
                continue

            if in_target_block:
                if inst["instruction"] == "push_offset" and inst["args"] and inst["args"][0] == "Voice":
                    raise ValueError(f"Found push_offset(Voice) in target block at label {label_name}, address {inst['address']}")

                if inst["instruction"].startswith("msg_::") and i >= 2 and instructions[i - 1]["instruction"] == "push_string" and instructions[i - 2]["instruction"] == "push_string":
                    speaker = instructions[i - 2]["args"][0]
                    text = instructions[i - 1]["args"][0]
                    cleaned = text_cleaning(text)

                    results.append({"Speaker": speaker, "Voice": voice, "Text": cleaned})

                    in_target_block = False
                    voice = None

            i += 1


def process_type1(data, results):
    '''
    line("D:\\WORKING\\NoSurfaceMoonRB\\BURIKOScriptSystem\\NoSurfaceMoon\\Script\\100_Converted\\D_0810_01.bsb", 506);
	push_dword(0);
	push_string("chk000329"); <== Voice
	push_dword(128);
	nargs(3);
	snd_::f_1a4();

	line("D:\\WORKING\\NoSurfaceMoonRB\\BURIKOScriptSystem\\NoSurfaceMoon\\Script\\100_Converted\\D_0810_01.bsb", 507);
	f_07b(0x12345678, 128, 25202);
	push_dword(1);
	push_dword(1);
	push_dword(0);
	push_string("千賀子"); <== Speaker
	push_string("「お前、それ本当にいい感じだぞ。ずーっとそのままでいて欲しいなぁ」"); <== Text
	msg_::f_140();
    '''
    labels = data.get("labels", {})

    for instructions in labels.values():
        in_target_block = False
        voice = None

        i = 0
        while i < len(instructions):
            inst = instructions[i]

            if inst["instruction"].startswith("snd_::f_1a4"):
                voice = None
                if instructions[i - 1]["instruction"] == "nargs":
                    # If nargs exists, voice is at position: i - nargs_value - 1
                    nargs_value = instructions[i - 1]["args"][0]
                    voice_index = i - nargs_value
                    if instructions[voice_index]["instruction"] == "push_string":
                        voice = instructions[voice_index]["args"][0]
                else:
                    # No nargs, voice is at fixed position: i-2
                    if instructions[i - 2]["instruction"] == "push_string":
                        voice = instructions[i - 2]["args"][0]

                in_target_block = True
                i += 1
                continue

            if in_target_block:
                if inst["instruction"].startswith("snd_::f_1a4"):
                    in_target_block = False
                    voice = None
                    continue

                if inst["instruction"].startswith("msg_::f_140") and i >= 2 and instructions[i - 1]["instruction"] == "push_string" and instructions[i - 2]["instruction"] == "push_string":
                    speaker = instructions[i - 2]["args"][0]
                    text = instructions[i - 1]["args"][0]
                    cleaned = text_cleaning(text)

                    results.append({"Speaker": speaker, "Voice": voice, "Text": cleaned})

                    in_target_block = False
                    voice = None

            i += 1


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
