import argparse
import os
import struct
from typing import Any, Dict, List, Optional, Tuple

MAGIC_CODE = b"@code:__"
MAGIC_MESS = b"@mess:__"
SCR_LINE_MAX = 4096  # aligns with C header


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=r"D:\Fuck_VN\script")
    parser.add_argument("--out-encoding", default="utf-8")
    parser.add_argument("--db-scripts", default=r"D:\Fuck_VN\data\db_scripts.bin")
    return parser.parse_args(args=args, namespace=namespace)


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
            # Prefer C-string style (NUL-terminated), fall back to next offset/text_size
            end = blob.find(b"\x00", off)
            if end == -1:
                # If no NUL, cut to next offset or blob end
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


# Opcode mapping (code -> (name, param_count, param_kinds))
# param_kinds: tuple of tokens among: 'i' (int32), 'f' (float32 bits), 'text' (index to text table), 'mess' (index into .001), 'pc' (code offset), 'proc' (proc id)
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
    # NAME takes an index into name_dat (db_scripts.bin "登場人物" sheet), not the local text table
    40: ("NAME", ("name",)),
    41: ("TEXT", ("mess",)),
    42: ("PAGE", ()),
    43: ("OPTION", ("text", "pc")),  # also pops one value from stack at runtime
    44: ("PROC", ("proc",)),
    45: ("LINE", ("i",)),
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
    # text offsets
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
    # Scrambled variant has header @mess:__
    if len(data) >= 8 and data[:8] == MAGIC_MESS:
        off = 8
        if off + 8 > len(data):
            raise ValueError(f"{path}: truncated after @mess:__ header")
        count, off = read_u32_le(data, off)
        size, off = read_u32_le(data, off)
        # Offsets
        offsets: List[int] = []
        for _ in range(count):
            val, off = read_u32_le(data, off)
            offsets.append(val)
        blob = bytearray(data[off : off + size])
        # Unscramble
        for i in range(len(blob)):
            blob[i] ^= 0x55
        # Extract C-strings using offsets
        entries: List[str] = []
        for i, start in enumerate(offsets):
            if start >= len(blob):
                entries.append("")
                continue
            end = blob.find(b"\x00", start)
            if end == -1:
                # fallback to next offset or end
                end = offsets[i + 1] if (i + 1) < len(offsets) else len(blob)
            try:
                entries.append(bytes(blob[start:end]).decode(encoding))
            except UnicodeDecodeError:
                entries.append(bytes(blob[start:end]).decode(encoding, errors="replace"))
        return MessFile(path, entries)
    else:
        # Plain text file: split lines on CR/LF
        try:
            txt = data.decode(encoding)
        except UnicodeDecodeError:
            txt = data.decode(encoding, errors="replace")
        # Normalize CRLF/CR/LF to LF then split
        txt = txt.replace("\r\n", "\n").replace("\r", "\n")
        entries = txt.split("\n")
        return MessFile(path, entries)


def find_peer_mess(bin_path: str) -> Optional[str]:
    base, _ = os.path.splitext(bin_path)
    cand = base + ".001"
    if os.path.isfile(cand):
        return cand
    # Also try uppercase/lowercase variants (Windows usually insensitive, but for portability)
    for ext in (".001", ".Mess", ".MESS"):
        cand = base + ext
        if os.path.isfile(cand):
            return cand
    return None


def load_proc_names(root: str) -> Dict[int, str]:
    proc_map: Dict[int, str] = {}
    adv_c = os.path.join(root, "adv", "adv.c")
    if not os.path.isfile(adv_c):
        return proc_map
    try:
        with open(adv_c, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        idx = 0
        for line in lines:
            line = line.strip()
            if line.startswith("set_proc("):
                # set_proc(proc_name);
                inside = line[len("set_proc(") :]
                inside = inside.split(")")[0]
                name = inside.strip()
                # Remove trailing comments if any
                name = name.split("//")[0].strip()
                if name:
                    proc_map[idx] = name
                    idx += 1
    except Exception:
        return {}
    return proc_map


def disassemble(bin_script: BinScript, mess: Optional[MessFile], out_path: str, out_encoding: str = "utf-8", db_scripts_path: Optional[str] = None) -> None:
    from mdb_parser import load_name_table, load_voice_table

    texts = bin_script.texts()
    proc_map = load_proc_names(os.getcwd())
    # Reverse map for quick lookup by name
    proc_rev: Dict[str, int] = {v: k for k, v in proc_map.items()}
    code = bin_script.code
    pc = 0
    lines: List[str] = []
    # Header
    lines.append(f"FILE: {os.path.basename(bin_script.path)}")
    lines.append(f"HEADER: code_size={bin_script.code_size} text_count={bin_script.text_count} text_size={bin_script.text_size} mess_count={bin_script.mess_count}")
    lines.append("")
    # Dump text table
    lines.append("TEXT_TABLE:")
    for i, s in enumerate(texts):
        # Escape newlines/tabs in display
        disp = s.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
        lines.append(f"  [{i}] {disp}")
    lines.append("")
    # Disassembly
    lines.append("CODE:")
    name_table = load_name_table(db_scripts_path)
    voc_table = load_voice_table(db_scripts_path)

    # Keep instruction history to recover proc arguments
    history: List[Tuple[int, str, List[Any]]] = []  # (pc0, op_name, raw_params)

    while pc < len(code):
        op = code[pc]
        op_name, kinds = OPCODES.get(op, (f"OP_{op}", ()))
        pc0 = pc
        pc += 1
        params: List[str] = []
        comments: List[str] = []
        raw_params: List[Any] = []
        for kind in kinds:
            if pc + 4 > len(code):
                params.append("<trunc>")
                break
            raw_i = struct.unpack_from("<i", code, pc)[0]
            raw_u = raw_i & 0xFFFFFFFF
            pc += 4
            if kind == "i":
                params.append(str(raw_i))
                raw_params.append(raw_i)
            elif kind == "f":
                val = read_f32_from_i32(raw_u)
                params.append(format(val, ".9g"))
                comments.append(f"bits=0x{raw_u:08X}")
                raw_params.append(val)
            elif kind == "text":
                idx = raw_u
                params.append(str(idx))
                if 0 <= idx < len(texts):
                    t = texts[idx].replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
                    comments.append(f"text='{t}'")
                else:
                    comments.append("text=<out_of_range>")
                raw_params.append(idx)
            elif kind == "name":
                idx = raw_u
                params.append(str(idx))
                if name_table and 0 <= idx < len(name_table):
                    nm = name_table[idx].replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
                    if nm:
                        comments.append(f"name='{nm}'")
                    else:
                        comments.append("name=<none>")
                raw_params.append(idx)
            elif kind == "mess":
                # Local index per file; map via .001 if present
                idx = raw_u
                params.append(str(idx))
                if mess and 0 <= idx < len(mess.entries):
                    m = mess.entries[idx].replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
                    comments.append(f"mess='{m}'")
                elif mess:
                    comments.append("mess=<out_of_range>")
                raw_params.append(idx)
            elif kind == "pc":
                params.append(str(raw_u))
                raw_params.append(raw_u)
            elif kind == "proc":
                name = proc_map.get(raw_u)
                if name:
                    params.append(f"{raw_u} ({name})")
                else:
                    params.append(str(raw_u))
                raw_params.append(raw_u)
            else:
                params.append(str(raw_u))
                raw_params.append(raw_u)

        # Append to history for potential backward analysis
        history.append((pc0, op_name, raw_params))

        # Extra annotation: decode PROC 26 (proc_cv) argument list into voice file names
        if op_name == "PROC":
            # Determine if this is proc_cv
            proc_id = int(raw_params[0]) if raw_params else None
            is_cv = False
            proc_name = proc_map.get(proc_id) if (proc_id is not None) else None
            if proc_name == "proc_cv":
                is_cv = True
            elif proc_rev.get("proc_cv", None) == proc_id:
                is_cv = True
            # Try also by common index 26 if no map
            if not is_cv and proc_id == 26 and ("proc_cv" in proc_map.values() or True):
                is_cv = True
            if is_cv:
                # Look back: last instruction should be PUSH_INT <count>
                # Collect up to 'count' preceding PUSH_* as args
                if len(history) >= 2:
                    count_instr = history[-2]
                    if count_instr[1] == "PUSH_INT" and count_instr[2]:
                        arg_count = int(count_instr[2][0])
                        args: List[int] = []
                        # Walk back to fetch preceding arg_count PUSH_* values
                        idx_hist = len(history) - 3
                        while idx_hist >= 0 and len(args) < arg_count:
                            hpc, hop, hparams = history[idx_hist]
                            if hop == "PUSH_INT" and hparams:
                                args.append(int(hparams[0]))
                            elif hop in ("PUSH_TEXT", "PUSH_MESS", "PUSH_FLOAT", "PUSH_GVAR", "PUSH_LVAR", "PUSH_RET"):
                                # We could try to resolve non-int to int, but keep it simple
                                args.append(None)  # type: ignore
                            else:
                                break
                            idx_hist -= 1
                        if args:
                            args = list(reversed(args))
                            # Build voice file annotations
                            VOC_MASK = 65536
                            voc_comments: List[str] = []
                            for a in args:
                                if isinstance(a, int) and a > 0:
                                    chr_idx = a // VOC_MASK
                                    idx = a % VOC_MASK
                                    if voc_table and 0 <= chr_idx < len(voc_table) and idx > 0:
                                        name_pref, subfolder, _group = voc_table[chr_idx]
                                        # Build path like voc\subfolder\name0001.ogg
                                        base_dir = "voc"
                                        path = f"{base_dir}\\{subfolder}\\{name_pref}{idx:04d}.ogg" if subfolder else f"{base_dir}\\{name_pref}{idx:04d}.ogg"
                                        voc_comments.append(path)
                                    else:
                                        voc_comments.append(f"id={a} (chr={chr_idx}, idx={idx})")
                                else:
                                    voc_comments.append("(arg)" if a is None else str(a))
                            if voc_comments:
                                comments.append("voices=" + ", ".join(voc_comments))

        if comments:
            lines.append(f"  {pc0:06d}: {op_name} " + ", ".join(params) + "    ; " + "; ".join(comments))
        else:
            lines.append(f"  {pc0:06d}: {op_name} " + ", ".join(params))
    # Write out
    with open(out_path, "w", encoding=out_encoding, newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def dump_mess(mess: MessFile, out_path: str, out_encoding: str = "utf-8") -> None:
    lines = []
    lines.append(f"FILE: {os.path.basename(mess.path)}")
    lines.append("MESSAGES:")
    for i, s in enumerate(mess.entries):
        disp = s.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
        lines.append(f"  [{i}] {disp}")
    with open(out_path, "w", encoding=out_encoding, newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def process_path(path: str, out_encoding: str, db_scripts_path: Optional[str] = None) -> List[str]:
    made: List[str] = []
    base = os.path.basename(path)
    _root, ext = os.path.splitext(base)
    parent = os.path.dirname(path)
    target_dir = parent
    os.makedirs(target_dir, exist_ok=True)

    ext_lower = ext.lower()
    if ext_lower == ".bin":
        b = parse_bin(path)
        mess_path = find_peer_mess(path)
        mess = parse_mess(mess_path) if mess_path else None
        out_path = os.path.join(target_dir, base + ".txt")
        disassemble(b, mess, out_path, out_encoding=out_encoding, db_scripts_path=db_scripts_path)
        made.append(out_path)
        if mess_path:
            mess_out = os.path.join(target_dir, os.path.basename(mess_path) + ".txt")
            if not os.path.exists(mess_out):
                dump_mess(parse_mess(mess_path), mess_out, out_encoding=out_encoding)
                made.append(mess_out)
    elif ext_lower == ".001":
        mess = parse_mess(path)
        out_path = os.path.join(target_dir, base + ".txt")
        dump_mess(mess, out_path, out_encoding=out_encoding)
        made.append(out_path)
    else:
        with open(path, "rb") as f:
            sig = f.read(8)
        if sig == MAGIC_CODE:
            return process_path(path[: -len(ext)] + ".bin", out_encoding, db_scripts_path)
        elif sig == MAGIC_MESS:
            return process_path(path[: -len(ext)] + ".001", out_encoding, db_scripts_path)
        else:
            raise ValueError(f"Unsupported file type: {path}")
    return made


if __name__ == "__main__":
    args = parse_args()

    outputs = []
    inp = args.input
    if os.path.isdir(inp):
        for root, _dirs, files in os.walk(inp):
            for fn in files:
                if fn.lower().endswith((".bin", ".001")):
                    p = os.path.join(root, fn)
                    try:
                        outputs += process_path(p, args.out_encoding, args.db_scripts)
                    except Exception as e:
                        print(f"[ERROR] {p}: {e}")
    else:
        print(f"[ERROR] {inp}: not a directory (only a single directory is allowed)")

    if outputs:
        print("Written:")
        for p in outputs:
            print("  ", p)
