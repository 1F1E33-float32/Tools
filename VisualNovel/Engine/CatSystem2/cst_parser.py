import argparse
import json
import zlib
from pathlib import Path

from cs2_utils import CS2_MAIN_OPCODES, Reader, tokenize_spaces


def extract_cst_with_meta(data):
    r = Reader(data)
    sig_raw = r.read(8)
    sig = sig_raw.rstrip(b"\x00").decode("ascii", errors="replace")
    if sig != "CatScene":
        raise ValueError(f"bad CST header signature: {sig}")
    comp_len = r.read_int32_le()
    decomp_len = r.read_int32_le()

    comp_data = r.read(comp_len)
    try:
        script_data = zlib.decompress(comp_data)
    except Exception as e:
        raise ValueError(f"zlib decompress failed: {e}")

    if len(script_data) != decomp_len:
        raise ValueError(f"decompress size mismatch: expected {decomp_len}, got {len(script_data)}")

    meta = {
        "header": sig,
        "encoding": {"mode": "zlib", "compressed_len": comp_len, "decompressed_len": decomp_len},
    }
    return script_data, meta


def parse_script_data(script_data):
    r = Reader(script_data)
    script_len = r.read_int32_le()
    input_count = r.read_int32_le()
    offset_table = r.read_int32_le()
    string_table = r.read_int32_le()

    SCRIPTHDR_SIZE = 16
    if script_len + SCRIPTHDR_SIZE != len(script_data):
        raise ValueError("corrupted script: script_len mismatch")

    entry_count = (string_table - offset_table) // 4

    r.pos = offset_table + SCRIPTHDR_SIZE
    offsets = [r.read_int32_le() for _ in range(entry_count)]

    lines = []
    for i in range(entry_count):
        r.pos = offsets[i] + string_table + SCRIPTHDR_SIZE
        line_type = r.read_uint16_le()
        content = r.read_terminated_string(encoding="shift_jis")
        lines.append({"type": line_type, "content": content})

    return {
        "scriptLength": script_len,
        "inputCount": input_count,
        "offsetTable": offset_table,
        "stringTable": string_table,
        "entryCount": entry_count,
        "lines": lines,
    }


def enrich_lines_with_items(lines):
    items = []
    for i, ln in enumerate(lines):
        content = ln["content"]
        line_type = ln["type"]

        if line_type == 0x3001:  # Command
            kind = "command"
            toks = tokenize_spaces(content)
            entry = {
                "index": i,
                "type": line_type,
                "kind": kind,
                "opcode": toks[0] if toks else None,
                "args": toks[1:] if len(toks) > 1 else [],
                "is_known": (toks[0] in CS2_MAIN_OPCODES) if toks else None,
            }
        elif line_type == 0x2001:  # Message
            kind = "message"
            entry = {"index": i, "type": line_type, "kind": kind, "text": content}
        elif line_type == 0x2101:  # Name
            kind = "name"
            entry = {"index": i, "type": line_type, "kind": kind, "name": content}
        elif line_type == 0x0201:  # Input
            kind = "input"
            entry = {"index": i, "type": line_type, "kind": kind}
        elif line_type == 0x0301:  # Page
            kind = "page"
            entry = {"index": i, "type": line_type, "kind": kind}
        else:
            raise ValueError("Unknown Type")
        items.append(entry)
    return items


def parse_cst_to_dict(data):
    script_data, meta = extract_cst_with_meta(data)
    script_info = parse_script_data(script_data)
    items = enrich_lines_with_items(script_info["lines"])

    return {
        **meta,
        "scriptLength": script_info["scriptLength"],
        "inputCount": script_info["inputCount"],
        "offsetTable": script_info["offsetTable"],
        "stringTable": script_info["stringTable"],
        "entryCount": script_info["entryCount"],
        "items": items,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=r"D:\Fuck_VN\script")
    args = p.parse_args()

    in_path = Path(args.input)
    for fp in in_path.glob("*.cst"):
        with fp.open("rb") as f:
            data = f.read()
        obj = parse_cst_to_dict(data)
        out_path = fp.with_suffix(".json")
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
