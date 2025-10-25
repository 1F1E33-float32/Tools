import argparse
import json
import os
import re
import struct

import bytefile


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, default=r"D:\Fuck_VN\rld_dec")
    parser.add_argument("--output", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = re.sub(r"《([^:》]+?)(?::[^》]+?)?》", r"\1", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("\ue000", "").replace("\n", "")
    return text


def parse_cmd(cmd):
    op = cmd & 0xFFFF
    int_cnt = (cmd >> 16) & 0xFF
    str_cnt = (cmd >> 24) & 0xF
    unk = cmd >> 28
    return op, int_cnt, str_cnt, unk


def parse_rld_header(stm):
    magic, unk1, unk2, inst_cnt, unk3 = struct.unpack("<4sIIII", stm.read(20))
    tag = stm.readstr()
    stm.seek(0x114)
    return {
        "magic": magic,
        "unk1": unk1,
        "unk2": unk2,
        "inst_cnt": inst_cnt,
        "unk3": unk3,
        "tag": tag,
    }


def build_name_table(defchara_path):
    names = {}
    pat = re.compile(r"^(\d+),(\d+),(\d+),([^,]+),")

    with open(defchara_path, "rb") as f:
        stm = bytefile.ByteFile(f.read())

    header = parse_rld_header(stm)

    for _ in range(header["inst_cnt"]):
        cmd_raw = stm.readu32()
        op, int_cnt, str_cnt, _ = parse_cmd(cmd_raw)
        _ = [stm.readu32() for _ in range(int_cnt)]
        strs = [stm.readstr() for _ in range(str_cnt)]

        if op != 48 or not strs:
            continue

        for s in strs:
            line = s.decode("cp932").strip()
            m = pat.match(line)
            if not m:
                continue
            char_id, _, _, name = m.groups()
            if not name or name.isdigit() or name.upper() == "NULL" or name.startswith("-"):
                continue
            names[int(char_id)] = name
    return names


def parse_rld(stm):
    header = parse_rld_header(stm)
    if header["magic"] != b"\x00DLR":
        raise ValueError("Not an RLD file")

    instructions = []
    for _ in range(header["inst_cnt"]):
        offset = stm.tell()
        cmd_raw = stm.readu32()
        op, int_cnt, str_cnt, unk = parse_cmd(cmd_raw)
        ints = [stm.readu32() for _ in range(int_cnt)]
        strs = [text_cleaning(stm.readstr().decode("cp932", errors="replace")) for _ in range(str_cnt)]

        ins = {"offset": offset, "cmd_raw": cmd_raw, "op": op, "unk": unk, "ints": ints, "strs": strs}
        instructions.append(ins)

    return {"header": header, "instructions": instructions}


def load_rld_dir(input_dir):
    result = {}
    for fname in os.listdir(input_dir):
        if not fname.endswith(".rld"):
            continue
        path = os.path.join(input_dir, fname)
        with open(path, "rb") as f:
            stm = bytefile.ByteFile(f.read())
        result[fname] = parse_rld(stm)
    return result


if __name__ == "__main__":
    args = parse_args()

    data = load_rld_dir(args.input_dir)
    defchara_path = os.path.join(args.input_dir, "defChara.rld")
    name_table = build_name_table(defchara_path)

    results = []
    for fname in data:
        instructions = data[fname]["instructions"]
        if len(instructions) > 0:
            for inst in instructions:
                if inst["op"] == 28:
                    Speaker = name_table.get(inst["ints"][0])
                    if Speaker:
                        Voice = inst["ints"][1]
                        Voice = str(Voice).zfill(5)
                        Text = inst["strs"][1]
                        results.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
