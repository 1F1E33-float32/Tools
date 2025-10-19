import argparse
import os
import re
from typing import Any, Dict, List, Tuple

HEX_RE = re.compile(r"0x[0-9a-fA-F]+")


def parse_int(s: str) -> int:
    s = s.strip()
    if s.startswith("-"):
        neg = True
        s2 = s[1:]
    else:
        neg = False
        s2 = s
    if HEX_RE.fullmatch(s2):
        val = int(s2, 16)
    else:
        val = int(s2, 10)
    return -val if neg else val


def load_vm_mapping(vm_txt_path: str) -> Dict[int, Dict[str, Any]]:
    with open(vm_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.rstrip("\n") for ln in f]

    # State machine: collect blocks per `case X:`
    blocks: Dict[int, List[str]] = {}
    cur: List[str] = []
    cur_case: int = -1

    case_re = re.compile(r"\bcase\s+(0x[0-9a-fA-F]+|\d+):")
    for ln in lines:
        m = case_re.search(ln)
        if m:
            # commit previous
            if cur_case != -1:
                blocks[cur_case] = cur
            cur = []
            cur_case = parse_int(m.group(1))
        if cur_case != -1:
            cur.append(ln)
    if cur_case != -1:
        blocks[cur_case] = cur

    mapping: Dict[int, Dict[str, Any]] = {}

    # Helpers
    def extract_idx_const(block: List[str]) -> Tuple[str, int]:
        # x9_1 = 0x... % arg5; OR x9_3 / x9_4
        idx_re = re.compile(r"x9_[134]\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*%\s*arg5;")
        for ln in block:
            m = idx_re.search(ln)
            if m:
                return ("idx", parse_int(m.group(1)))
        raise ValueError("idx const not found in block")

    def extract_header_offset(block: List[str], reg: str) -> int:
        # reg is like x10_14 / x10_31 / x10_12 / x10_29 / x10_7
        hdr_re = re.compile(rf"{re.escape(reg)}\s*=\s*arg3\[(0x[0-9a-fA-F]+|\d+)\];")
        for ln in block:
            m = hdr_re.search(ln)
            if m:
                return parse_int(m.group(1))
        raise ValueError(f"header offset for {reg} not found")

    def extract_const(block: List[str], reg: str) -> int:
        c_re = re.compile(rf"{re.escape(reg)}\s*=\s*(-?0x[0-9a-fA-F]+|-?\d+);")
        for ln in block:
            m = c_re.search(ln)
            if m:
                return parse_int(m.group(1))
        raise ValueError(f"const {reg} not found")

    # Parse each case
    for opc, blk in blocks.items():
        # Base index const
        _, idx_const = extract_idx_const(blk)

        block_text = "\n".join(blk)

        # 1) Swap family via label_1917498
        if "label_1917498" in block_text:
            off = extract_header_offset(blk, "x10_14")
            cst = extract_const(blk, "x11_6")
            mapping[opc] = {"type": "SWAP", "idx_const": idx_const, "off": off, "cst": cst}
            continue

        # 2) Coupled-decrement via label_1917568
        if "label_1917568" in block_text:
            off = extract_header_offset(blk, "x10_7")
            cst = extract_const(blk, "x11_4")
            mapping[opc] = {"type": "COUPLED_DEC", "idx_const": idx_const, "off": off, "cst": cst}
            continue

        # 3) Rotations
        if "label_19174e4" in block_text:
            # xor 4 then 19174e8
            off = extract_header_offset(blk, "x10_31")
            mapping[opc] = {"type": "ROT_XOR4", "idx_const": idx_const, "off": off}
            continue
        if "label_19174e8" in block_text and "x10_306 = arg3[" in block_text:
            off = extract_header_offset(blk, "x10_306")
            mapping[opc] = {"type": "ROT_SH", "idx_const": idx_const, "off": off}
            continue
        if "label_1917190" in block_text:
            off = extract_header_offset(blk, "x10_12")
            mapping[opc] = {"type": "ROT_PLUS1", "idx_const": idx_const, "off": off}
            continue
        if "label_191716c" in block_text:
            off = extract_header_offset(blk, "x10_29")
            mapping[opc] = {"type": "ROT_GENERIC", "idx_const": idx_const, "off": off, "delta": -1}
            continue
        if "label_19175e0" in block_text:
            off = extract_header_offset(blk, "x10_29")
            mapping[opc] = {"type": "ROT_GENERIC", "idx_const": idx_const, "off": off, "delta": +2}
            continue
        if "label_19175bc" in block_text:
            off = extract_header_offset(blk, "x10_29")
            mapping[opc] = {"type": "ROT_GENERIC", "idx_const": idx_const, "off": off, "delta": +3}
            continue
        if "label_1917604" in block_text:
            off = extract_header_offset(blk, "x10_29")
            mapping[opc] = {"type": "ROT_GENERIC", "idx_const": idx_const, "off": off, "delta": +5}
            continue
        if "label_1916da8" in block_text:
            off = extract_header_offset(blk, "x10_29")
            mapping[opc] = {"type": "ROT_GENERIC", "idx_const": idx_const, "off": off, "delta": +6}
            continue

        # 4) Direct ops on *(arg4 + idx)
        # EON-like: ^= ~arg3[off]
        m = re.search(r"\*\(arg4 \+ x9_[134]\) \^= ~arg3\[(0x[0-9a-fA-F]+|\d+)\];", block_text)
        if m:
            off = parse_int(m.group(1))
            mapping[opc] = {"type": "XOR_NOT_HEADER", "idx_const": idx_const, "off": off}
            continue

        # EON-like variant: = *(...) ^ ~arg3[off]
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) \^ ~arg3\[(0x[0-9a-fA-F]+|\d+)\];", block_text)
        if m:
            off = parse_int(m.group(1))
            mapping[opc] = {"type": "XOR_NOT_HEADER", "idx_const": idx_const, "off": off}
            continue

        # XOR header ^ imm using ^= form
        m = re.search(r"\*\(arg4 \+ x9_[134]\) \^= arg3\[(0x[0-9a-fA-F]+|\d+)\] \^ (0x[0-9a-fA-F]+|\d+);", block_text)
        if m:
            off = parse_int(m.group(1))
            imm = parse_int(m.group(2))
            mapping[opc] = {"type": "XOR_HDR_IMM", "idx_const": idx_const, "off": off, "imm": imm}
            continue

        # XOR header ^ imm using = form
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) \^ arg3\[(0x[0-9a-fA-F]+|\d+)\] \^ (0x[0-9a-fA-F]+|\d+);", block_text)
        if m:
            off = parse_int(m.group(1))
            imm = parse_int(m.group(2))
            mapping[opc] = {"type": "XOR_HDR_IMM", "idx_const": idx_const, "off": off, "imm": imm}
            continue

        # XOR header only using ^= form
        m = re.search(r"\*\(arg4 \+ x9_[134]\) \^= arg3\[(0x[0-9a-fA-F]+|\d+)\];", block_text)
        if m:
            off = parse_int(m.group(1))
            mapping[opc] = {"type": "XOR_HDR", "idx_const": idx_const, "off": off}
            continue

        # XOR header only using = form
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) \^ arg3\[(0x[0-9a-fA-F]+|\d+)\];", block_text)
        if m:
            off = parse_int(m.group(1))
            mapping[opc] = {"type": "XOR_HDR", "idx_const": idx_const, "off": off}
            continue

        # Special: ^ *arg3 ^ imm (i.e., header[0] ^ imm)
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) \^ \*arg3 \^ (0x[0-9a-fA-F]+|\d+);", block_text)
        if m:
            imm = parse_int(m.group(1))
            mapping[opc] = {"type": "XOR_HDR0_IMM", "idx_const": idx_const, "imm": imm}
            continue

        # SUB header +/- imm
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) - arg3\[(0x[0-9a-fA-F]+|\d+)\] ([+-]) (0x[0-9a-fA-F]+|\d+);", block_text)
        if m:
            off = parse_int(m.group(1))
            sign = m.group(2)
            imm = parse_int(m.group(3))
            k = imm if sign == "+" else -imm
            mapping[opc] = {"type": "SUB_HDR_IMM", "idx_const": idx_const, "off": off, "imm": k}
            continue

        # SUB header only
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) - arg3\[(0x[0-9a-fA-F]+|\d+)\];", block_text)
        if m:
            off = parse_int(m.group(1))
            mapping[opc] = {"type": "SUB_HDR_IMM", "idx_const": idx_const, "off": off, "imm": 0}
            continue

        # If we get here, try more additive forms: add-only (rare), or mixed
        # add-only pattern (not observed, but safe): + imm
        m = re.search(r"\*\(arg4 \+ x9_[134]\) = \*\(arg4 \+ x9_[134]\) \+ (0x[0-9a-fA-F]+|\d+);", block_text)
        if m:
            imm = parse_int(m.group(1))
            mapping[opc] = {"type": "ADD_IMM", "idx_const": idx_const, "imm": imm}
            continue

        # Fallback: if nothing matched, raise to surface
        raise RuntimeError(f"Unparsed opcode case {opc:#x}\n{block_text}")

    return mapping


def rol8(x: int, s: int) -> int:
    s &= 7
    return ((x << s) | (x >> (8 - s))) & 0xFF


def ror8(x: int, s: int) -> int:
    s &= 7
    return ((x >> s) | (x << (8 - s))) & 0xFF


def apply_one(op: Dict[str, Any], header: bytearray, block: bytearray, width: int) -> None:
    idx = op["idx_const"] % width
    t = op["type"]

    if t == "SWAP":
        off = op["off"] & 0xFF
        cst = op["cst"]
        h = header[off]
        idx2 = (h + (cst % width)) % width
        block[idx], block[idx2] = block[idx2], block[idx]
        return

    if t == "COUPLED_DEC":
        off = op["off"] & 0xFF
        cst = op["cst"]
        h = header[off]
        idx2 = (h + (cst % width)) % width
        b2 = (block[idx2] - 1) & 0xFF
        block[idx] = (block[idx] - b2) & 0xFF
        block[idx2] = b2
        return

    if t == "ROT_XOR4":
        off = op["off"] & 0xFF
        s = (header[off] ^ 0x04) & 7
        block[idx] = ror8(block[idx], s)
        return

    if t == "ROT_SH":
        off = op["off"] & 0xFF
        s = header[off] & 7
        block[idx] = ror8(block[idx], s)
        return

    if t == "ROT_PLUS1":
        off = op["off"] & 0xFF
        h = header[off]
        s = (h + 1) & 7
        block[idx] = ror8(block[idx], s)
        return

    if t == "ROT_GENERIC":
        off = op["off"] & 0xFF
        delta = op["delta"]
        h = header[off]
        s = (h + delta) & 7
        block[idx] = ror8(block[idx], s)
        return

    if t == "XOR_HDR_IMM":
        off = op["off"] & 0xFF
        imm = op["imm"] & 0xFF
        block[idx] ^= (header[off] ^ imm) & 0xFF
        return

    if t == "XOR_HDR":
        off = op["off"] & 0xFF
        block[idx] ^= header[off]
        return

    if t == "XOR_NOT_HEADER":
        off = op["off"] & 0xFF
        block[idx] ^= (~header[off]) & 0xFF
        return

    if t == "XOR_HDR0_IMM":
        imm = op["imm"] & 0xFF
        block[idx] ^= (header[0] ^ imm) & 0xFF
        return

    if t == "SUB_HDR_IMM":
        off = op["off"] & 0xFF
        imm = op["imm"] & 0xFF
        block[idx] = (block[idx] - header[off] + imm) & 0xFF
        return

    if t == "ADD_IMM":
        imm = op["imm"] & 0xFF
        block[idx] = (block[idx] + imm) & 0xFF
        return

    raise RuntimeError(f"Unknown op type {t}")


def vm_apply_block(program_40: bytes, header_256: bytes, block_bytes: bytearray, mapping: Dict[int, Dict[str, Any]]) -> None:
    width = len(block_bytes)
    header = bytearray(header_256)
    for t in range(0x40):
        opcode = program_40[t]
        op = mapping.get(opcode)
        if op is None:
            raise RuntimeError(f"No mapping for opcode {opcode:#x}")
        apply_one(op, header, block_bytes, width)


def decrypt_file(input_path: str, output_path: str, vm_txt_path: str) -> None:
    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    magic = int.from_bytes(data[0:4], "little")
    if magic != 0x1357FEDA:
        raise RuntimeError(f"Bad magic: {magic:#x}")

    data_len = int.from_bytes(data[4:8], "little")
    header = bytes(data[0x08:0x108])
    program = bytes(data[0x108 : 0x108 + 0x40])

    start = 0x148
    end = start + data_len
    if end > len(data):
        raise RuntimeError("Declared data length exceeds file size")

    payload = data[start:end]

    mapping = load_vm_mapping(vm_txt_path)

    off = 0
    while off < len(payload):
        chunk_len = min(0x40, len(payload) - off)
        chunk = payload[off : off + chunk_len]
        vm_apply_block(program, header, chunk, mapping)
        payload[off : off + chunk_len] = chunk
        off += chunk_len

    marker = bytes(payload[0:8])
    if marker != b"CODEPHIL":
        raise RuntimeError(f"Marker check failed: got {marker!r}")

    data[start:end] = payload

    with open(output_path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default=r"C:\Users\bfloat16\Downloads\YostarGames\StellaSora_CN\xtlr_Data\il2cpp_data\Metadata\global-metadata.dat")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--vm", default=r"OnlineGame\Unity\StellaSora\vm.txt")
    args = parser.parse_args()

    inp = os.path.abspath(args.input)
    outp = args.output or os.path.join(os.path.dirname(inp), "global-metadata.dec.dat")
    vm_p = os.path.abspath(args.vm)

    decrypt_file(inp, outp, vm_p)
    print(f"Decryption OK. Output: {outp}")