import argparse
import json
import os
import struct

import asdis
import bgiop


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", default=r"E:\VN\ja\AUGUST\Daitoshokan no Hitsujikai\script")
    return parser.parse_args()


def get_code_end(data):
    pos = -1
    while 1:
        res = data.find(b"\xf4\x00\x00\x00", pos + 1)
        if res == -1:
            break
        pos = res
    return pos + 4


def parse_hdr(hdr):
    hdrtext = hdr[:0x1C].rstrip(b"\x00").decode("cp932")
    defines = {}

    unknown1 = struct.unpack("<I", hdr[0x20:0x24])[0]

    if unknown1 == 0:
        # 旧版本格式: 0x20是unknown1, 0x24是entries
        (entries,) = struct.unpack("<I", hdr[0x24:0x28])
        pos = 0x28
    else:
        # 新版本格式: 0x20直接是entries (没有unknown1字段)
        entries = unknown1
        pos = 0x24

    for k in range(entries):
        pos1 = hdr.find(b"\x00", pos)
        name = hdr[pos:pos1].decode("cp932")
        pos = pos1 + 1
        (offset,) = struct.unpack("<I", hdr[pos : pos + 4])
        defines[offset] = name
        pos += 4
    return hdrtext, defines


def parse(code, hdr):
    if hdr:
        hdrtext, defines = parse_hdr(hdr)
    else:
        hdrtext = None
        defines = {}
    bgiop.clear_offsets()
    inst = {}
    size = get_code_end(code)
    pos = 0
    while pos < size:
        addr = pos
        (op,) = struct.unpack("<I", code[addr : addr + 4])
        if op not in bgiop.ops:
            raise Exception(("size unknown for op %02x @ offset %05x" % (op, addr)))
        pos += 4
        fmt, pfmt, fcn = bgiop.ops[op]
        if fmt:
            n = struct.calcsize(fmt)
            args = struct.unpack(fmt, code[pos : pos + n])
            if fcn:
                args = fcn(code, addr, defines, *args)
            inst[addr] = pfmt % args
            pos += n
        else:
            inst[addr] = pfmt
    offsets = bgiop.offsets.copy()
    return inst, offsets, hdrtext, defines


def parse_instruction(inst_str):
    import re

    # Match function_name(args)
    match = re.match(r"([A-Za-z_][A-Za-z0-9_:]*)\((.*)\)", inst_str)
    if match:
        name = match.group(1)
        args_str = match.group(2)
        if args_str:
            # Parse arguments - handle strings, numbers, labels
            args = []
            # Simple argument parsing - split by comma outside quotes
            in_quotes = False
            current_arg = ""
            for char in args_str:
                if char == '"' and (not current_arg or current_arg[-1] != "\\"):
                    in_quotes = not in_quotes
                    current_arg += char
                elif char == "," and not in_quotes:
                    args.append(current_arg.strip())
                    current_arg = ""
                else:
                    current_arg += char
            if current_arg:
                args.append(current_arg.strip())

            # Convert arguments to appropriate types
            parsed_args = []
            for arg in args:
                if arg.startswith('"') and arg.endswith('"'):
                    # String argument - keep as is (remove quotes)
                    parsed_args.append(arg[1:-1])
                elif arg.startswith("L") or (arg and arg[0].isupper()):
                    # Label reference
                    parsed_args.append(arg)
                elif arg.startswith("0x"):
                    # Hex number
                    parsed_args.append(int(arg, 16))
                elif arg.lstrip("-").isdigit():
                    # Decimal number
                    parsed_args.append(int(arg))
                else:
                    # Keep as string
                    parsed_args.append(arg)
            return name, parsed_args
        else:
            return name, []
    else:
        # No parentheses - just the instruction name
        return inst_str, []


def render_txt(fo, inst, offsets, hdrtext, defines):
    if hdrtext:
        fo.write('#header "%s"\n\n' % asdis.escape(hdrtext))
    if defines:
        for offset in sorted(defines):
            fo.write("#define %s L%05x\n" % (defines[offset], offset))
        fo.write("\n")
    for addr in sorted(inst):
        if inst[addr].startswith("line("):
            fo.write("\n")
        if addr in offsets or addr in defines:
            if addr in defines:
                fo.write("\n%s:\n" % defines[addr])
            else:
                fo.write("\nL%05x:\n" % addr)
        fo.write("\t%s;\n" % inst[addr])


def render_json(fo, inst, offsets, hdrtext, defines):
    # Build instruction list
    instructions = []
    for addr in sorted(inst):
        inst_name, inst_args = parse_instruction(inst[addr])
        entry = {
            "address": addr,
            "instruction": inst_name,
            "args": inst_args,
        }
        instructions.append(entry)

    # Build labels dictionary: label_name -> [instructions]
    # Labels include both named labels (from defines) and offset labels (from offsets)
    labels = {}
    current_label = None
    label_instructions = []

    for entry in instructions:
        addr = entry["address"]

        # Check if this address has a label (either named or offset)
        is_label = addr in offsets or addr in defines

        if is_label:
            # Save previous label if exists
            if current_label is not None:
                labels[current_label] = label_instructions

            # Determine label name
            if addr in defines:
                current_label = defines[addr]
            else:
                current_label = "L%05x" % addr

            # Start new label with this instruction
            label_instructions = [entry]
        else:
            # Add to current label's instructions
            if current_label is not None:
                label_instructions.append(entry)

    # Save last label
    if current_label is not None:
        labels[current_label] = label_instructions

    output = {"header": hdrtext, "defines": [{"name": defines[offset], "offset": offset} for offset in sorted(defines)], "labels": labels}
    json.dump(output, fo, ensure_ascii=False, indent=4)


def dis(file):
    fi = open(file, "rb")
    hdr_test = fi.read(0x20)
    if hdr_test.startswith(b"BurikoCompiledScriptVer1.00\x00"):
        hdrsize = 0x1C + struct.unpack("<I", hdr_test[0x1C:0x20])[0]
    else:
        hdrsize = 0
    fi.seek(0, 0)
    hdr = fi.read(hdrsize)
    code = fi.read()
    fi.close()

    # Parse to IR
    inst, offsets, hdrtext, defines = parse(code, hdr)

    # Render to txt format
    txt_file = os.path.splitext(file)[0] + ".txt"
    with open(txt_file, "w", encoding="utf-8") as fo:
        render_txt(fo, inst, offsets, hdrtext, defines)

    # Render to json format
    json_file = os.path.splitext(file)[0] + ".json"
    with open(json_file, "w", encoding="utf-8") as fo:
        render_json(fo, inst, offsets, hdrtext, defines)


if __name__ == "__main__":
    args = parse_args()

    for item in os.listdir(args.in_dir):
        file_path = os.path.join(args.in_dir, item)
        base, ext = os.path.splitext(item)
        if not ext and os.path.isfile(file_path):
            print(f"Disassembling {file_path}...")
            dis(file_path)
