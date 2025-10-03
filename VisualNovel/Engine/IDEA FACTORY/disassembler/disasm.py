import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional

from stcm2 import STCM2_MAGIC, ParameterKind
from stcm2 import from_bytes as stcm2_from_bytes
from tqdm import tqdm


@dataclass
class StringType:
    kind: Literal["String", "U32"]
    u32: Optional[int]
    type_flag: int
    data: Optional[bytes] = None

    def type_(self) -> int:
        return self.type_flag


def autolabel(prefix: str, addr: int) -> bytes:
    return f"{prefix}_{addr:X}".encode("ascii")


def decode_with_hex_replacement(buf: bytes) -> str:
    try:
        return buf.decode("utf-8", "strict")
    except UnicodeDecodeError:
        pass
    try:
        return buf.decode("cp932", "strict")
    except UnicodeDecodeError:
        pass

    out_chars: List[str] = []
    i = 0
    n = len(buf)
    while i < n:
        b0 = buf[i]
        if b0 < 0x80:
            out_chars.append(chr(b0))
            i += 1
            continue
        # Determine UTF-8 sequence length
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
            out_chars.append("\U0001f5ffX" + f"{b0:02x}")
            i += 1
            continue

        out_chars.append(chr(cp_val))
        i += need + 1

    return "".join(out_chars)


def label_to_string(label: bytes) -> str:
    out = []
    for b in label:
        if (0x21 <= b <= 0x5B) or (0x5D <= b <= 0x7E):
            out.append(chr(b))
        else:
            out.append("\\x" + f"{b:02x}")
    return "".join(out)


def decode_string(addr: int, data: bytes):
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

    if len(str_bytes) == 4:
        n = int.from_bytes(str_bytes, "little")
        return StringType("U32", n, type_), tail

    if type_ != 0:
        raise ValueError("string type is 1, but is not a u32")

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


def chunk_actions(acts):
    chunks = []
    current_labels = set()
    current_chunk = []

    for addr in sorted(acts.keys()):
        act = acts[addr]
        current_labels.add(addr)
        for p in act.params:
            if p.kind == ParameterKind.ACTION_REF:
                current_labels.add(p.value)
        current_chunk.append((addr, act))
        if (not act.call) and act.opcode == 0:
            chunks.append((set(current_labels), list(current_chunk)))
            current_labels.clear()
            current_chunk.clear()

    if current_chunk:
        chunks.append((set(current_labels), list(current_chunk)))

    cur = 0
    while cur + 1 < len(chunks):
        while True:
            merged = False
            for i in range(len(chunks) - 1, cur, -1):
                if not chunks[cur][0].isdisjoint(chunks[i][0]):
                    h0, v0 = chunks[cur]
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


@dataclass
class DisasmParam:
    kind: Literal["Value", "ActionRef", "GlobalDataPointer", "DataPointer"]
    value: Optional[int] = None
    ref_addr_hex: Optional[str] = None
    ref_label: Optional[str] = None
    offset: Optional[int] = None
    data_val: Optional[StringType] = None


@dataclass
class DisasmInst:
    addr: int
    label_bytes: Optional[bytes]
    call: bool
    opcode: int
    call_target_label: Optional[str]
    params: List[DisasmParam]
    junk: bytes


@dataclass
class FunctionIR:
    name: str
    instructions: List[DisasmInst]


@dataclass
class ModuleIR:
    tag: str
    global_data: bytes
    functions: List[FunctionIR]


@dataclass
class DisasmConfig:
    mnemonics: Dict[int, str]
    print_junk: bool = False
    show_address: bool = False


def build_ir(file_bytes: bytes) -> ModuleIR:
    stcm2 = stcm2_from_bytes(file_bytes)

    # 1) autolabel
    autolabels: Dict[int, bytes] = {}
    for act in stcm2.actions.values():
        # fn_ for call targets without export
        if act.call:
            tgt = stcm2.actions.get(act.opcode)
            if tgt and tgt.export is None:
                prev = autolabels.get(act.opcode)
                if prev is None or not prev.startswith(b"fn"):
                    autolabels[act.opcode] = autolabel("fn", act.opcode)
        # local_ for internal action refs without export
        for p in act.params:
            if p.kind == ParameterKind.ACTION_REF:
                a = p.value
                tgt = stcm2.actions.get(a)
                if tgt and tgt.export is None:
                    prev = autolabels.get(a)
                    if prev in (None, b""):
                        autolabels[a] = autolabel("local", a)

    # apply autolabels
    if autolabels:
        for addr in sorted(autolabels.keys()):
            act = stcm2.actions.get(addr)
            if act is None:
                raise ValueError("this should never happen 1")
            if act.export is not None:
                raise ValueError("this should never happen 2")
            act.export = autolabels[addr]

    print_junk = False  # rendering时再决定是否显示
    tag = stcm2.tag.decode("utf-8", "ignore").rstrip("\x00")

    functions: List[FunctionIR] = []
    last_fn: Optional[str] = None

    # 2) chunk into functions
    for chunk in chunk_actions(stcm2.actions):
        if not chunk:
            continue

        # name decision for the chunk
        head_addr, head_act = chunk[0]
        head_label_bytes = head_act.label(print_junk)
        fname: Optional[str] = None
        if head_label_bytes:
            head_label = label_to_string(head_label_bytes).strip()
            if not head_label.startswith("local_"):
                fname = head_label
        if fname is None:
            fname = last_fn or f"fn_0x{head_addr:X}"
        if fname.strip().startswith("local_"):
            fname = last_fn or f"fn_0x{head_addr:X}"

        insts: List[DisasmInst] = []

        # 3) per instruction: scan data records and build params
        for addr, act in chunk:
            if addr == 504608:
                pass
            if addr == 509640:
                pass
            data = act.data
            pos = 0
            at_beginning = True
            data_pos = {}
            base_offset = 0
            junk = b""

            while pos < len(data):
                try:
                    s, tail = decode_string(pos, data)
                except Exception:
                    pos += 1
                    continue

                if pos != 0:
                    if not at_beginning:
                        raise ValueError("junk found after beginning")
                    junk = data[:pos]
                at_beginning = False

                # absolute offset within the original act.data
                abs_pos = base_offset + pos
                data_pos[abs_pos] = s

                consumed = len(data) - len(tail)
                base_offset += consumed
                data = tail
                pos = 0

            if data:
                if not at_beginning:
                    raise ValueError("junk found after beginning")
                junk = data

            # params -> IR
            params_ir: List[DisasmParam] = []
            for p in act.params:
                if p.kind == ParameterKind.VALUE:
                    params_ir.append(DisasmParam(kind="Value", value=p.value))
                elif p.kind == ParameterKind.ACTION_REF:
                    tgt = stcm2.actions.get(p.value)
                    if tgt is None or tgt.label(print_junk) is None:
                        raise ValueError("bruh5")
                    params_ir.append(DisasmParam(kind="ActionRef", ref_addr_hex=f"{p.value:X}", ref_label=label_to_string(tgt.label(print_junk))))
                elif p.kind == ParameterKind.DATA_POINTER:
                    s = data_pos.get(p.value)
                    if s is None:
                        raise ValueError("param references non-string")
                    params_ir.append(DisasmParam(kind="DataPointer", data_val=s))
                elif p.kind == ParameterKind.GLOBAL_DATA_POINTER:
                    params_ir.append(DisasmParam(kind="GlobalDataPointer", offset=p.value))

            # action kind
            call_target_label = None
            if act.call:
                tgt = stcm2.actions.get(act.opcode)
                if tgt is None or tgt.label(print_junk) is None:
                    raise ValueError("bruh")
                call_target_label = label_to_string(tgt.label(print_junk))

            insts.append(DisasmInst(addr=addr, label_bytes=act.label(print_junk), call=act.call, opcode=act.opcode, call_target_label=call_target_label, params=params_ir, junk=junk))

        functions.append(FunctionIR(name=fname, instructions=insts))

        # update last_fn
        if head_label_bytes:
            head_label = label_to_string(head_label_bytes).strip()
            if not head_label.startswith("local_"):
                last_fn = fname
        if last_fn is None:
            last_fn = fname

    return ModuleIR(tag=tag, global_data=stcm2.global_data, functions=functions)


def render_text(mod: ModuleIR, config: DisasmConfig) -> str:
    mnemonics = config.mnemonics
    print_junk = config.print_junk
    show_address = config.show_address

    out_lines: List[str] = []
    out_lines.append(f'.tag "{mod.tag}"')
    b64 = base64.b64encode(mod.global_data).decode("ascii").rstrip("=")
    out_lines.append(f".global_data {b64}")
    out_lines.append(".code_start")

    # compute label width
    all_labels: List[bytes] = []
    for fn in mod.functions:
        for inst in fn.instructions:
            if inst.label_bytes:
                all_labels.append(inst.label_bytes)
    maxlabel = max((len(label) for label in all_labels), default=0)
    maxlabel = max(maxlabel, 14)

    for fn in mod.functions:
        out_lines.append("")  # blank line between chunks
        for inst in fn.instructions:
            parts: List[str] = []
            if show_address:
                parts.append(f"0x{inst.addr:06X} ")

            if inst.label_bytes is not None:
                label = label_to_string(inst.label_bytes)
                parts.append(f"{label:>{maxlabel}}: ")
            else:
                parts.append(f"{'':{maxlabel}}  ")

            # mnemonic/call/raw
            if inst.call:
                parts.append("call " + (inst.call_target_label or ""))
            elif inst.opcode in mnemonics:
                parts.append(mnemonics[inst.opcode])
            else:
                parts.append(f"raw {inst.opcode:X}")

            # parameters
            for p in inst.params:
                if p.kind == "Value":
                    parts.append(f", {p.value:X}")
                elif p.kind == "ActionRef":
                    parts.append(", [" + (p.ref_label or p.ref_addr_hex or "") + "]")
                elif p.kind == "GlobalDataPointer":
                    parts.append(f", [global_data+{p.offset:X}]")
                elif p.kind == "DataPointer":
                    s = p.data_val
                    if s is None:
                        raise ValueError("missing DataPointer value")
                    if s.kind == "U32":
                        prefix = "" if s.type_() == 0 else "@"
                        n = s.u32 or 0
                        if n < 0x10000000:
                            parts.append(f", {prefix}={n}")
                        else:
                            parts.append(f", {prefix}={n:X}h")
                    else:
                        sdec = decode_with_hex_replacement(s.data or b"")
                        escaped = []
                        for ch in sdec:
                            o = ord(ch)
                            if o < 32:
                                escaped.append("\\x" + f"{o:02x}")
                            elif ch == "\U0001f5ff":
                                escaped.append("\\")
                            elif ch in ('"', "\\"):
                                escaped.append("\\" + ch)
                            else:
                                escaped.append(ch)
                        parts.append(', "' + "".join(escaped) + '"')

            if print_junk and inst.junk:
                j64 = base64.b64encode(inst.junk).decode("ascii").rstrip("=")
                parts.append(" ! " + j64)

            out_lines.append("".join(parts))

    return "\n".join(out_lines) + "\n"


def render_json(mod: ModuleIR, config: DisasmConfig) -> str:
    mnemonics = config.mnemonics
    include_addr = config.show_address

    code_start = {}

    for fn in mod.functions:
        inst_list = []
        for inst in fn.instructions:

            def params_to_json():
                out = []
                for p in inst.params:
                    if p.kind == "Value":
                        out.append({"type": "Value", "value": p.value or 0})
                    elif p.kind == "ActionRef":
                        item = {"type": "ActionRef"}
                        if p.ref_addr_hex is not None:
                            item["addr"] = p.ref_addr_hex
                        if p.ref_label is not None:
                            item["label"] = p.ref_label
                        out.append(item)
                    elif p.kind == "GlobalDataPointer":
                        out.append({"type": "GlobalDataPointer", "offset": p.offset or 0})
                    elif p.kind == "DataPointer":
                        s = p.data_val
                        if s is None:
                            raise ValueError("param references non-string")
                        if s.kind == "U32":
                            u32_val = s.u32 or 0
                            out.append({"type": "DataPointer", "u32": u32_val, "u32_type": s.type_()})
                        else:
                            sdec = decode_with_hex_replacement(s.data or b"")
                            out.append({"type": "DataPointer", "string": sdec})
                return out

            base = {"params": params_to_json()}
            if include_addr:
                base["addr"] = f"0x{inst.addr:06X}"
            if inst.label_bytes:
                base["label"] = label_to_string(inst.label_bytes)

            if inst.call:
                base.update({"action": "call", "target": inst.call_target_label or ""})
            else:
                if inst.opcode in mnemonics:
                    base.update({"action": mnemonics[inst.opcode]})
                else:
                    base.update({"action": "opcode", "target": inst.opcode})

            inst_list.append(base)

        code_start.setdefault(fn.name, []).extend(inst_list)

    out = {"tag": mod.tag, "global_data_b64": base64.b64encode(mod.global_data).decode("ascii").rstrip("="), "code_start": code_start}
    return json.dumps(out, ensure_ascii=False, indent=2)


def disasm_run(
    in_dir: Path,
    mnemonics: Dict[int, str],
    print_junk: bool = False,
    show_address: bool = False,
    emit_txt: bool = True,
    emit_json: bool = True,
):
    in_dir = Path(in_dir)
    cfg = DisasmConfig(mnemonics=mnemonics, print_junk=print_junk, show_address=show_address)

    for path in tqdm(in_dir.rglob("*.DAT"),ncols=150):
        if not path.is_file():
            continue

        file_bytes = path.read_bytes()
        if len(file_bytes) < len(STCM2_MAGIC) or file_bytes[: len(STCM2_MAGIC)] != STCM2_MAGIC:
            continue

        ir = build_ir(file_bytes)

        if emit_txt:
            txt = render_text(ir, cfg)
            path.with_suffix(".txt").write_text(txt, encoding="utf-8")

        if emit_json:
            js = render_json(ir, cfg)
            path.with_suffix(".json").write_text(js, encoding="utf-8")
