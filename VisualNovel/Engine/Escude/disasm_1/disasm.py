import os
import struct
from typing import Any, Dict, List, Optional, Tuple

MAGIC_CODE = b"@code:__"
MAGIC_MESS = b"@mess:__"
SCR_LINE_MAX = 4096


class BinScript:
    def __init__(self, path: str, code: bytes, text_offsets: List[int], text_blob: bytes, code_size: int, text_count: int, text_size: int, mess_count: int):
        self.path = path
        self.code = code
        self.text_offsets = text_offsets
        self.text_blob = text_blob
        self.code_size = code_size
        self.text_count = text_count
        self.text_size = text_size
        self.mess_count = mess_count

    def texts(self, encoding: str = "cp932") -> List[str]:
        res = []
        blob = self.text_blob
        n = len(blob)
        for i, off in enumerate(self.text_offsets):
            if off < 0 or off >= n:
                res.append("")
                continue
            end = blob.find(b"\x00", off)
            if end == -1:
                if i + 1 < len(self.text_offsets):
                    end = self.text_offsets[i + 1]
                else:
                    end = n
            try:
                res.append(blob[off:end].decode(encoding))
            except UnicodeDecodeError:
                res.append(blob[off:end].decode(encoding, errors="replace"))
        return res


class MessFile:
    def __init__(self, path: str, entries: List[str]):
        self.path = path
        self.entries = entries


OPCODES: Dict[int, Tuple[str, Tuple[str, ...]]] = {
    1: ("POP", ()),
    2: ("POP_N", ("i",)),
    3: ("POP_RET", ()),
    4: ("PUSH_INT", ("i",)),
    5: ("PUSH_FLOAT", ("f",)),
    6: ("PUSH_RET", ()),
    7: ("PUSH_TEXT", ("text",)),
    8: ("PUSH_MESS", ("mess",)),
    9: ("PUSH_GVAR", ("i",)),
    10: ("PUSH_LVAR", ("i",)),
    11: ("STORE_GVAR", ("i",)),
    12: ("STORE_LVAR", ("i",)),
    13: ("ENTER", ("i",)),
    14: ("LEAVE", ()),
    15: ("JMP", ("pc",)),
    16: ("JMPZ", ("pc",)),
    17: ("CALL", ("pc",)),
    18: ("RET", ()),
    19: ("LOG_OR", ()),
    20: ("LOG_AND", ()),
    21: ("LOG_NOT", ()),
    22: ("OR", ()),
    23: ("XOR", ()),
    24: ("AND", ()),
    25: ("NOT", ()),
    26: ("CMP_EQ", ()),
    27: ("CMP_NE", ()),
    28: ("CMP_LT", ()),
    29: ("CMP_LE", ()),
    30: ("CMP_GT", ()),
    31: ("CMP_GE", ()),
    32: ("SHL", ()),
    33: ("SHR", ()),
    34: ("ADD", ()),
    35: ("SUB", ()),
    36: ("MUL", ()),
    37: ("DIV", ()),
    38: ("MOD", ()),
    39: ("NEG", ()),
    40: ("NAME", ("name",)),
    41: ("TEXT", ("mess",)),
    42: ("PAGE", ()),
    43: ("OPTION", ("text", "pc")),
    44: ("PROC", ("proc",)),
    45: ("LINE", ("i",)),
}


class Instruction:
    def __init__(self, pc: int, opcode: int, op_name: str, params: List[Any], param_kinds: Tuple[str, ...], param_comments: List[Optional[Any]], extra_comment: Optional[List[str]]):
        self.pc = pc
        self.opcode = opcode
        self.op_name = op_name
        self.params = params
        self.param_kinds = param_kinds
        self.param_comments = param_comments
        self.extra_comment = extra_comment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pc": self.pc,
            "opcode": self.opcode,
            "op_name": self.op_name,
            "params": self.params,
            "param_kinds": list(self.param_kinds),
            "param_comments": self.param_comments,
            "extra_comment": self.extra_comment
        }


class ScriptIR:
    def __init__(self, bin_script: BinScript, mess: Optional[MessFile], instructions: List[Instruction]):
        self.bin_script = bin_script
        self.mess = mess
        self.instructions = instructions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": os.path.basename(self.bin_script.path),
            "header": {
                "code_size": self.bin_script.code_size,
                "text_count": self.bin_script.text_count,
                "text_size": self.bin_script.text_size,
                "mess_count": self.bin_script.mess_count
            },
            "texts": self.bin_script.texts(),
            "mess_entries": self.mess.entries if self.mess else [],
            "instructions": [inst.to_dict() for inst in self.instructions]
        }


def read_u32_le(b: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<I", b, off)[0], off + 4


def read_i32_le(b: bytes, off: int) -> Tuple[int, int]:
    return struct.unpack_from("<i", b, off)[0], off + 4


def read_f32_from_i32(i: int) -> float:
    return struct.unpack("<f", struct.pack("<I", i & 0xFFFFFFFF))[0]


def parse_bin(path: str) -> BinScript:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 8 or data[:8] != MAGIC_CODE:
        raise ValueError(f"{path}: missing @code:__ header")
    off = 8
    code_size, off = read_u32_le(data, off)
    text_count, off = read_u32_le(data, off)
    text_size, off = read_u32_le(data, off)
    mess_count, off = read_u32_le(data, off)
    if off + code_size > len(data):
        raise ValueError(f"{path}: code_size exceeds file")
    code = data[off : off + code_size]
    off += code_size
    text_offsets: List[int] = []
    for _ in range(text_count):
        if off + 4 > len(data):
            raise ValueError(f"{path}: text_offset out of range")
        val, off = read_u32_le(data, off)
        text_offsets.append(val)
    if off + text_size > len(data):
        raise ValueError(f"{path}: text_size exceeds file")
    text_blob = data[off : off + text_size]
    return BinScript(path, code, text_offsets, text_blob, code_size, text_count, text_size, mess_count)


def parse_mess(path: str, encoding: str = "cp932") -> MessFile:
    with open(path, "rb") as f:
        data = f.read()
    if len(data) >= 8 and data[:8] == MAGIC_MESS:
        off = 8
        if off + 8 > len(data):
            raise ValueError(f"{path}: truncated after @mess:__ header")
        count, off = read_u32_le(data, off)
        size, off = read_u32_le(data, off)
        offsets: List[int] = []
        for _ in range(count):
            val, off = read_u32_le(data, off)
            offsets.append(val)
        blob = bytearray(data[off : off + size])
        for i in range(len(blob)):
            blob[i] ^= 0x55
        entries: List[str] = []
        for i, start in enumerate(offsets):
            if start >= len(blob):
                entries.append("")
                continue
            end = blob.find(b"\x00", start)
            if end == -1:
                end = offsets[i + 1] if (i + 1) < len(offsets) else len(blob)
            try:
                entries.append(bytes(blob[start:end]).decode(encoding))
            except UnicodeDecodeError:
                entries.append(bytes(blob[start:end]).decode(encoding, errors="replace"))
        return MessFile(path, entries)
    else:
        try:
            txt = data.decode(encoding)
        except UnicodeDecodeError:
            txt = data.decode(encoding, errors="replace")
        txt = txt.replace("\r\n", "\n").replace("\r", "\n")
        entries = txt.split("\n")
        return MessFile(path, entries)


def find_peer_mess(bin_path: str) -> Optional[str]:
    base, _ = os.path.splitext(bin_path)
    cand = base + ".001"
    if os.path.isfile(cand):
        return cand
    for ext in (".001", ".Mess", ".MESS"):
        cand = base + ext
        if os.path.isfile(cand):
            return cand
    return None


def load_proc_names(root: str) -> Dict[int, str]:
    proc_map = {}
    adv_c = os.path.join(root, "exe", "adv", "adv.c")
    with open(adv_c, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    idx = 0
    for line in lines:
        line = line.strip()
        if line.startswith("set_proc("):
            inside = line[len("set_proc(") :]
            inside = inside.split(")")[0]
            name = inside.strip()
            name = name.split("//")[0].strip()
            if name:
                proc_map[idx] = name
                idx += 1
    return proc_map


def decompile_to_ir(bin_script: BinScript, mess: Optional[MessFile], root: str, name_table: List[str], voc_table: List[Tuple[str, str, str]]) -> ScriptIR:
    texts = bin_script.texts()
    proc_map = load_proc_names(root)
    code = bin_script.code
    pc = 0
    instructions: List[Instruction] = []
    history = []

    while pc < len(code):
        op = code[pc]
        op_name, kinds = OPCODES.get(op, (f"OP_{op}", ()))
        pc0 = pc
        pc += 1
        params: List[Any] = []

        for kind in kinds:
            if pc + 4 > len(code):
                params.append(None)
                break
            raw_i = struct.unpack_from("<i", code, pc)[0]
            raw_u = raw_i & 0xFFFFFFFF
            pc += 4

            if kind == "i":
                params.append(raw_i)
            elif kind == "f":
                val = read_f32_from_i32(raw_u)
                params.append(val)
            elif kind in ("text", "mess", "name", "pc", "proc"):
                params.append(raw_u)
            else:
                params.append(raw_u)

        param_comments = []
        for i, kind in enumerate(kinds):
            if i >= len(params):
                param_comments.append(None)
                continue

            raw_val = params[i]
            if raw_val is None:
                param_comments.append(None)
                continue

            if kind == "f":
                bits = struct.unpack("<I", struct.pack("<f", raw_val))[0]
                param_comments.append(f"0x{bits:08X}")
            elif kind == "text":
                idx = raw_val
                if 0 <= idx < len(texts):
                    param_comments.append(texts[idx])
                else:
                    param_comments.append("<out_of_range>")
            elif kind == "name":
                idx = raw_val
                if name_table and 0 <= idx < len(name_table):
                    nm = name_table[idx]
                    param_comments.append(nm if nm else "<none>")
                else:
                    param_comments.append(None)
            elif kind == "mess":
                idx = raw_val
                if mess and 0 <= idx < len(mess.entries):
                    param_comments.append(mess.entries[idx])
                elif mess:
                    param_comments.append("<out_of_range>")
                else:
                    param_comments.append(None)
            elif kind == "proc":
                name = proc_map.get(raw_val)
                param_comments.append(name)
            else:
                param_comments.append(None)

        history.append((pc0, op_name, params))

        extra_comment = None
        if op_name == "PROC":
            proc_id = int(params[0]) if params else None
            proc_name = proc_map.get(proc_id)
            if proc_name == "proc_cv":
                if len(history) >= 2:
                    count_instr = history[-2]
                    if count_instr[1] == "PUSH_INT" and count_instr[2]:
                        arg_count = int(count_instr[2][0])
                        args: List[int] = []
                        idx_hist = len(history) - 3
                        while idx_hist >= 0 and len(args) < arg_count:
                            _, hop, hparams = history[idx_hist]
                            if hop == "PUSH_INT" and hparams:
                                args.append(int(hparams[0]))
                            elif hop in ("PUSH_TEXT", "PUSH_MESS", "PUSH_FLOAT", "PUSH_GVAR", "PUSH_LVAR", "PUSH_RET"):
                                args.append(None)
                            else:
                                break
                            idx_hist -= 1
                        if args:
                            args = list(reversed(args))
                            VOC_MASK = 65536
                            voc_paths: List[str] = []
                            for a in args:
                                if isinstance(a, int) and a > 0:
                                    chr_idx = a // VOC_MASK
                                    idx = a % VOC_MASK
                                    if 0 <= chr_idx < len(voc_table) and idx > 0:
                                        name_pref, subfolder, _ = voc_table[chr_idx]
                                        path = f"{subfolder}\\{name_pref}{idx:04d}.ogg"
                                        voc_paths.append(path)
                                    else:
                                        raise ValueError(f"Invalid voice table entry: chr_idx={chr_idx}, idx={idx}")
                                else:
                                    raise ValueError(f"Invalid voice argument: {a}")
                            extra_comment = voc_paths

        inst = Instruction(pc0, op, op_name, params, kinds, param_comments, extra_comment)
        instructions.append(inst)

    return ScriptIR(bin_script, mess, instructions)


def process_file(path: str, root: str, name_table: List[str], voc_table: List[Tuple[str, str, str]]) -> ScriptIR:
    base = os.path.basename(path)
    _, ext = os.path.splitext(base)

    ext_lower = ext.lower()
    if ext_lower == ".bin":
        bin_script = parse_bin(path)
        mess_path = find_peer_mess(path)
        mess = parse_mess(mess_path) if mess_path else None
        return decompile_to_ir(bin_script, mess, root, name_table, voc_table)
    elif ext_lower == ".001":
        mess = parse_mess(path)
        empty_bin = BinScript(path, b"", [], b"", 0, 0, 0, len(mess.entries))
        return ScriptIR(empty_bin, mess, [])
    else:
        with open(path, "rb") as f:
            sig = f.read(8)
        if sig == MAGIC_CODE:
            return process_file(path[: -len(ext)] + ".bin", root, name_table, voc_table)
        elif sig == MAGIC_MESS:
            return process_file(path[: -len(ext)] + ".001", root, name_table, voc_table)
        else:
            raise ValueError(f"Unsupported file type: {path}")
