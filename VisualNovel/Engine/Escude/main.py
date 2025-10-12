import argparse
import json
import os

from decompile import process_file
from mdb_parser import load_name_table, load_voice_table


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=r"D:\Fuck_VN")
    parser.add_argument("--out-encoding", default="utf-8")
    return parser.parse_args(args=args, namespace=namespace)


def ir_to_txt(ir, out_path, out_encoding):
    lines = []
    lines.append(f"FILE: {os.path.basename(ir.bin_script.path)}")
    lines.append(f"HEADER: code_size={ir.bin_script.code_size} text_count={ir.bin_script.text_count} text_size={ir.bin_script.text_size} mess_count={ir.bin_script.mess_count}")
    lines.append("")
    lines.append("TEXT_TABLE:")
    for i, s in enumerate(ir.bin_script.texts()):
        disp = s.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
        lines.append(f"  [{i}] {disp}")
    lines.append("")
    lines.append("CODE:")

    for inst in ir.instructions:
        pc = inst.pc
        op_name = inst.op_name
        raw_params = inst.params
        kinds = inst.param_kinds
        param_comments = inst.param_comments
        extra_comment = inst.extra_comment

        params = []
        comments = []

        for i, kind in enumerate(kinds):
            if i >= len(raw_params):
                params.append("<missing>")
                continue

            raw_val = raw_params[i]
            if raw_val is None:
                params.append("<trunc>")
                continue

            if kind == "i":
                params.append(str(raw_val))
            elif kind == "f":
                params.append(format(raw_val, ".9g"))
                if param_comments[i]:
                    comments.append(param_comments[i])
            elif kind == "text":
                params.append(str(raw_val))
                if param_comments[i]:
                    t = param_comments[i].replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
                    comments.append(f"'{t}'")
            elif kind == "name":
                params.append(str(raw_val))
                if param_comments[i]:
                    nm = param_comments[i].replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
                    comments.append(f"'{nm}'")
            elif kind == "mess":
                params.append(str(raw_val))
                if param_comments[i]:
                    m = param_comments[i].replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
                    comments.append(f"'{m}'")
            elif kind == "pc":
                params.append(str(raw_val))
            elif kind == "proc":
                if param_comments[i]:
                    params.append(f"{raw_val} ({param_comments[i]})")
                else:
                    params.append(str(raw_val))
            else:
                params.append(str(raw_val))

        if extra_comment:
            comments.append(", ".join(extra_comment))

        if comments:
            lines.append(f"  {pc:06d}: {op_name} " + ", ".join(params) + "    ; " + "; ".join(comments))
        else:
            lines.append(f"  {pc:06d}: {op_name} " + ", ".join(params))

    with open(out_path, "w", encoding=out_encoding, newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def ir_to_json(ir, out_path, out_encoding):
    with open(out_path, "w", encoding=out_encoding) as f:
        json.dump(ir.to_dict(), f, ensure_ascii=False, indent=2)


def dump_mess_txt(ir, out_path, out_encoding):
    if not ir.mess:
        return
    lines = []
    lines.append(f"FILE: {os.path.basename(ir.mess.path)}")
    lines.append("MESSAGES:")
    for i, s in enumerate(ir.mess.entries):
        disp = s.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
        lines.append(f"  [{i}] {disp}")
    with open(out_path, "w", encoding=out_encoding, newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def process_path(path, out_encoding, root, name_table, voc_table):
    made = []
    base = os.path.basename(path)
    _, ext = os.path.splitext(base)
    parent = os.path.dirname(path)
    target_dir = parent
    os.makedirs(target_dir, exist_ok=True)

    ext_lower = ext.lower()

    ir = process_file(path, root, name_table, voc_table)

    if ext_lower == ".bin":
        out_txt = os.path.join(target_dir, base + ".txt")
        ir_to_txt(ir, out_txt, out_encoding)
        made.append(out_txt)

        out_json = os.path.join(target_dir, base + ".json")
        ir_to_json(ir, out_json, out_encoding)
        made.append(out_json)

        if ir.mess:
            mess_out = os.path.join(target_dir, os.path.basename(ir.mess.path) + ".txt")
            if not os.path.exists(mess_out):
                dump_mess_txt(ir, mess_out, out_encoding)
                made.append(mess_out)

    elif ext_lower == ".001":
        out_txt = os.path.join(target_dir, base + ".txt")
        dump_mess_txt(ir, out_txt, out_encoding)
        made.append(out_txt)
    return made


if __name__ == "__main__":
    args = parse_args()

    outputs = []
    inp = args.input
    db_scripts_path = os.path.join(inp, "data", "db_scripts.bin")
    name_table = load_name_table(db_scripts_path)
    voc_table = load_voice_table(db_scripts_path)

    script_dir = os.path.join(inp, "script")
    if os.path.isdir(script_dir):
        for root, _, files in os.walk(script_dir):
            for fn in files:
                if fn.lower().endswith((".bin", ".001")):
                    p = os.path.join(root, fn)
                    try:
                        outputs += process_path(p, args.out_encoding, inp, name_table, voc_table)
                    except Exception as e:
                        print(f"[ERROR] {p}: {e}")
    else:
        print(f"[ERROR] {script_dir}: not a directory")