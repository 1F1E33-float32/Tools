# Reference: https://github.com/robbie01/stcm2-asm

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from stcm2 import STCM2_MAGIC, Action, ParameterKind
from stcm2 import from_bytes as stcm2_from_bytes


@dataclass
class StringType:
    kind: str  # "String" or "U32"
    u32: Optional[int]
    type_flag: int  # 0 or 1
    data: Optional[bytes] = None

    def type_(self) -> int:
        return self.type_flag


def autolabel(prefix: str, addr: int) -> bytes:
    return f"{prefix}_0x{addr:X}".encode("ascii")


def _decode_utf8_with_hex_replacement(buf: bytes) -> str:
    # Fast path
    try:
        return buf.decode("utf-8", "strict")
    except UnicodeDecodeError:
        pass

    # Manual UTF-8 decode; replace every invalid byte with "\U0001F5FFX{b:02x}"
    out_chars: List[str] = []
    i = 0
    n = len(buf)
    while i < n:
        b0 = buf[i]
        if b0 < 0x80:
            out_chars.append(chr(b0))
            i += 1
            continue
        # Determine sequence length
        if 0xC2 <= b0 <= 0xDF:
            need = 1
            min_cp = 0x80
            cp = b0 & 0x1F
        elif 0xE0 <= b0 <= 0xEF:
            need = 2
            min_cp = 0x800
            cp = b0 & 0x0F
        elif 0xF0 <= b0 <= 0xF4:
            need = 3
            min_cp = 0x10000
            cp = b0 & 0x07
        else:
            out_chars.append("\U0001f5ffX" + f"{b0:02x}")
            i += 1
            continue

        if i + need >= n:
            # Truncated sequence => treat bytes individually
            out_chars.append("\U0001f5ffX" + f"{b0:02x}")
            i += 1
            continue

        ok = True
        cp_val = cp
        for j in range(1, need + 1):
            bj = buf[i + j]
            if bj & 0xC0 != 0x80:
                ok = False
                break
            cp_val = (cp_val << 6) | (bj & 0x3F)

        if not ok or cp_val < min_cp or cp_val > 0x10FFFF or (0xD800 <= cp_val <= 0xDFFF):
            # Invalid sequence: emit each byte as replacement
            out_chars.append("\U0001f5ffX" + f"{b0:02x}")
            i += 1
            continue

        out_chars.append(chr(cp_val))
        i += need + 1

    return "".join(out_chars)


def decode_with_hex_replacement(buf: bytes) -> str:
    # Try UTF-8 first
    try:
        return buf.decode("utf-8", "strict")
    except UnicodeDecodeError:
        pass
    # Then try CP932 (Windows-31J)
    try:
        return buf.decode("cp932", "strict")
    except UnicodeDecodeError:
        pass
    # Fallback to robust UTF-8-like decode with hex replacement
    return _decode_utf8_with_hex_replacement(buf)


def label_to_string(label: bytes) -> str:
    # Allowed: bytes in ranges 0x21..0x5B and 0x5D..0x7E
    out = []
    for b in label:
        if (0x21 <= b <= 0x5B) or (0x5D <= b <= 0x7E):
            out.append(chr(b))
        else:
            out.append("\\x" + f"{b:02x}")
    return "".join(out)


def decode_string(addr: int, data: bytes) -> Tuple[StringType, bytes]:
    # addr is an offset into data
    if addr < 0 or addr > len(data):
        raise ValueError("addr out of bounds")
    s = memoryview(data)[addr:]
    if len(s) <= 16:
        raise ValueError("not enough room for magic")

    type_ = int.from_bytes(s[0:4], "little")
    if type_ not in (0, 1):
        raise ValueError("string magic isn't 0 or 1")
    qlen = int.from_bytes(s[4:8], "little")
    if int.from_bytes(s[8:12], "little") != 1:
        raise ValueError("string magic isn't 1")
    length = int.from_bytes(s[12:16], "little")
    if length != qlen * 4:
        raise ValueError(f"len and qlen are inconsistent: len = {length}, qlen = {qlen}")

    if len(s) < 16 + length:
        raise ValueError("not enough room for string data")

    str_bytes = s[16 : 16 + length].tobytes()
    tail = s[16 + length :].tobytes()

    # Try u32 heuristic
    if len(str_bytes) == 4:
        n = int.from_bytes(str_bytes, "little")
        if type_ == 1 or not (0x100000 <= n < 0x1000000 or n == 28783):
            if type_ == 0:
                return StringType("U32", n, 0), tail
            else:
                return StringType("U32", n, 1), tail

    if type_ != 0:
        raise ValueError("string type is 1, but is not a u32")

    # Trim trailing zeros (1..=4)
    nzero = 0
    for b in reversed(str_bytes):
        if b == 0:
            nzero += 1
        else:
            break
    if not (1 <= nzero <= 4):
        raise ValueError("string is not canonical")
    str_bytes = str_bytes[: len(str_bytes) - nzero]

    return StringType("String", None, 0, data=str_bytes), tail


def chunk_actions(acts: Dict[int, Action]) -> List[List[Tuple[int, Action]]]:
    # Heuristically determine function boundaries by splitting on returns,
    # and combining based on labels and local jumps.
    chunks: List[Tuple[set[int], List[Tuple[int, Action]]]] = []
    current_labels: set[int] = set()
    current_chunk: List[Tuple[int, Action]] = []

    for addr in sorted(acts.keys()):
        act = acts[addr]
        current_labels.add(addr)
        for param in act.params:
            if param.kind == ParameterKind.ACTION_REF:
                current_labels.add(param.value)
        current_chunk.append((addr, act))
        if (not act.call) and act.opcode == 0:
            chunks.append((set(current_labels), list(current_chunk)))
            current_labels.clear()
            current_chunk.clear()

    if current_chunk:
        chunks.append((set(current_labels), list(current_chunk)))

    cur = 0
    while cur + 1 < len(chunks):
        # Merge overlapping label sets.
        while True:
            merged = False
            for i in range(len(chunks) - 1, cur, -1):
                if not chunks[cur][0].isdisjoint(chunks[i][0]):
                    h0, v0 = chunks[cur]
                    # Union all from cur+1..i
                    for j in range(cur + 1, i + 1):
                        h0 |= chunks[j][0]
                        v0 += chunks[j][1]
                    chunks[cur] = (h0, v0)
                    del chunks[cur + 1 : i + 1]
                    merged = True
                    break
            if not merged:
                break
        cur += 1

    return [v for _, v in chunks]


def disassemble_to_string(file_bytes: bytes) -> str:
    stcm2 = stcm2_from_bytes(file_bytes)

    # build symbol table and autolabels
    autolabels: Dict[int, bytes] = {}
    for act in stcm2.actions.values():
        if act.call and stcm2.actions.get(act.opcode) and stcm2.actions[act.opcode].export is None:
            ent = autolabels.get(act.opcode)
            if not ent or not ent.startswith(b"fn"):
                autolabels[act.opcode] = autolabel("fn", act.opcode)
        for param in act.params:
            if param.kind == ParameterKind.ACTION_REF:
                addr = param.value
                if stcm2.actions.get(addr) and stcm2.actions[addr].export is None:
                    if autolabels.get(addr) in (None, b""):
                        autolabels[addr] = autolabel("local", addr)

    if autolabels:
        for addr in sorted(autolabels.keys()):
            act = stcm2.actions.get(addr)
            if act is None:
                raise ValueError("this should never happen 1")
            if act.export is not None:
                raise ValueError("this should never happen 2")
            act.export = autolabels[addr]

    out_lines: List[str] = []

    tag = stcm2.tag.decode("utf-8", "ignore").rstrip("\x00")
    out_lines.append(f'.tag "{tag}"')
    b64 = base64.b64encode(stcm2.global_data).decode("ascii").rstrip("=")
    out_lines.append(f".global_data {b64}")
    out_lines.append(".code_start")

    print_junk = False
    show_address = False

    def get_label(act: Action) -> Optional[bytes]:
        return act.label(print_junk)

    try:
        maxlabel = max((len(get_label(act)) for act in stcm2.actions.values() if get_label(act)), default=0)
    except ValueError:
        maxlabel = 0
    maxlabel = max(maxlabel, 14)

    for chunk in chunk_actions(stcm2.actions):
        out_lines.append("")
        for addr, act in chunk:
            line_parts: List[str] = []
            if show_address:
                line_parts.append(f"0x{addr:06X} ")

            label_bytes = act.label(print_junk)
            if label_bytes is not None:
                label = label_to_string(label_bytes)
                line_parts.append(f"{label:>{maxlabel}}: ")
            else:
                line_parts.append(f"{'':{maxlabel}}  ")

            if act.call:
                target = stcm2.actions.get(act.opcode)
                if target is None or target.label(print_junk) is None:
                    raise ValueError("bruh")
                line_parts.append("call " + label_to_string(target.label(print_junk)))
            elif (not act.call) and act.opcode == 0 and len(act.params) == 0:
                line_parts.append("return")
            else:
                line_parts.append(f"raw 0x{act.opcode:X}")

            data = act.data
            pos = 0
            junk = b""
            at_beginning = True
            data_pos: Dict[int, StringType] = {}
            base_offset = 0
            while pos < len(data):
                try:
                    s, tail = decode_string(pos, data)
                except Exception:
                    pos += 1
                    continue
                # found a string at pos
                if pos != 0:
                    if not at_beginning:
                        raise ValueError("junk found after beginning")
                    junk = data[:pos]
                at_beginning = False

                abs_pos = base_offset + pos
                data_pos[abs_pos] = s

                consumed = len(data) - len(tail)
                # Update base_offset and data to tail
                base_offset += consumed
                data = tail
                pos = 0
            if data:
                if not at_beginning:
                    raise ValueError("junk found after beginning")
                junk = data

            for p in act.params:
                if p.kind == ParameterKind.VALUE:
                    line_parts.append(f", 0x{p.value:X}")
                elif p.kind == ParameterKind.ACTION_REF:
                    tgt = stcm2.actions.get(p.value)
                    if tgt is None or tgt.label(print_junk) is None:
                        raise ValueError("bruh5")
                    line_parts.append(", [" + label_to_string(tgt.label(print_junk)) + "]")
                elif p.kind == ParameterKind.DATA_POINTER:
                    s = data_pos.get(p.value)
                    if s is None:
                        raise ValueError("param references non-string")
                    if s.kind == "U32":
                        prefix = "" if s.type_() == 0 else "@"
                        n = s.u32 if s.u32 is not None else 0
                        if n < 0x10000000:
                            line_parts.append(f", {prefix}=0x{n:X}")
                        else:
                            line_parts.append(f", {prefix}=0x{n:X}h")
                    else:
                        sdec = decode_with_hex_replacement(s.data or b"")
                        # Escape
                        escaped = []
                        for ch in sdec:
                            if ord(ch) < 32:
                                escaped.append("\\x" + f"{ord(ch):02x}")
                            elif ch == "\U0001f5ff":
                                escaped.append("\\")
                            elif ch in ('"', "\\"):
                                escaped.append("\\" + ch)
                            else:
                                escaped.append(ch)
                        line_parts.append(', "' + "".join(escaped) + '"')
                elif p.kind == ParameterKind.GLOBAL_DATA_POINTER:
                    line_parts.append(f", [global_data+0x{p.value:X}]")

            if print_junk and junk:
                j64 = base64.b64encode(junk).decode("ascii").rstrip("=")
                line_parts.append(" ! " + j64)

            out_lines.append("".join(line_parts))

    return "\n".join(out_lines) + "\n"


def disassemble_to_json(file_bytes: bytes) -> str:
    stcm2 = stcm2_from_bytes(file_bytes)

    # build symbol table and autolabels (same as text output)
    autolabels: Dict[int, bytes] = {}
    for act in stcm2.actions.values():
        if act.call and stcm2.actions.get(act.opcode) and stcm2.actions[act.opcode].export is None:
            ent = autolabels.get(act.opcode)
            if not ent or not ent.startswith(b"fn"):
                autolabels[act.opcode] = autolabel("fn", act.opcode)
        for p in act.params:
            if p.kind == ParameterKind.ACTION_REF:
                a = p.value
                if stcm2.actions.get(a) and stcm2.actions[a].export is None:
                    if autolabels.get(a) in (None, b""):
                        autolabels[a] = autolabel("local", a)

    if autolabels:
        for addr in sorted(autolabels.keys()):
            act = stcm2.actions.get(addr)
            if act is None:
                raise ValueError("this should never happen 1")
            if act.export is not None:
                raise ValueError("this should never happen 2")
            act.export = autolabels[addr]

    print_junk = False
    tag = stcm2.tag.decode("utf-8", "ignore").rstrip("\x00")

    code_start: Dict[str, List[dict]] = {}
    last_fn: Optional[str] = None

    for chunk in chunk_actions(stcm2.actions):
        if not chunk:
            continue
        head_addr, head_act = chunk[0]
        head_label_bytes = head_act.label(print_junk)
        fname: Optional[str] = None
        if head_label_bytes:
            head_label = label_to_string(head_label_bytes).strip()
            if not head_label.startswith("local_"):
                fname = head_label
        if fname is None:
            fname = last_fn or f"fn_0x{head_addr:X}"
        # Final guard: never allow a local_* name to become a function key.
        if fname.strip().startswith("local_"):
            fname = last_fn or f"fn_0x{head_addr:X}"

        inst_list: List[dict] = []

        for addr, act in chunk:
            data = act.data
            pos = 0
            at_beginning = True
            data_pos: Dict[int, StringType] = {}
            base_offset = 0

            while pos < len(data):
                try:
                    s, tail = decode_string(pos, data)
                except Exception:
                    pos += 1
                    continue
                if pos != 0:
                    if not at_beginning:
                        raise ValueError("junk found after beginning")
                at_beginning = False

                abs_pos = base_offset + pos
                data_pos[abs_pos] = s

                consumed = len(data) - len(tail)
                base_offset += consumed
                data = tail
                pos = 0

            def build_params() -> List[dict]:
                params_json: List[dict] = []
                for p in act.params:
                    if p.kind == ParameterKind.VALUE:
                        params_json.append({"type": "Value", "value": f"0x{p.value:X}"})
                    elif p.kind == ParameterKind.ACTION_REF:
                        params_json.append({"type": "ActionRef", "addr": f"0x{p.value:X}"})
                    elif p.kind == ParameterKind.GLOBAL_DATA_POINTER:
                        params_json.append({"type": "GlobalDataPointer", "offset": f"0x{p.value:X}"})
                    elif p.kind == ParameterKind.DATA_POINTER:
                        s = data_pos.get(p.value)
                        if s is None:
                            raise ValueError("param references non-string")
                        if s.kind == "U32":
                            u32_val = s.u32 if s.u32 is not None else 0
                            params_json.append({"type": "DataPointer", "u32": f"0x{u32_val:X}", "u32_type": s.type_()})
                        else:
                            sdec = decode_with_hex_replacement(s.data or b"")
                            params_json.append({"type": "DataPointer", "string": sdec})
                return params_json

            if act.call:
                tgt = stcm2.actions.get(act.opcode)
                if tgt is None or tgt.label(print_junk) is None:
                    raise ValueError("bruh")
                inst_list.append({
                    "action": "call",
                    "target": label_to_string(tgt.label(print_junk)),
                    "params": build_params(),
                })
            elif (not act.call) and act.opcode == 0 and len(act.params) == 0:
                inst_list.append({"action": "return"})
            else:
                inst_list.append({
                    "action": "opcode",
                    "target": f"0x{act.opcode:X}",
                    "params": build_params(),
                })

        if fname in code_start:
            code_start[fname].extend(inst_list)
        else:
            code_start[fname] = inst_list

        if head_label_bytes:
            head_label = label_to_string(head_label_bytes).strip()
            if not head_label.startswith("local_"):
                last_fn = fname
        if last_fn is None:
            last_fn = fname

    out = {
        "tag": tag,
        "global_data_b64": base64.b64encode(stcm2.global_data).decode("ascii").rstrip("="),
        "code_start": code_start,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


def run(in_dir: Path) -> None:
    in_dir = Path(in_dir)
    for path in in_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            with open(path, "rb") as f:
                header = f.read(len(STCM2_MAGIC))
            if header != STCM2_MAGIC:
                continue

            file_bytes = path.read_bytes()
            try:
                text = disassemble_to_string(file_bytes)
                json_s = disassemble_to_json(file_bytes)
            except Exception:
                # Header matched but parsing failed; skip this file
                continue

            path.with_suffix(".txt").write_text(text, encoding="utf-8")
            path.with_suffix(".json").write_text(json_s, encoding="utf-8")
        except Exception:
            # IO or other unexpected error; skip file
            continue
