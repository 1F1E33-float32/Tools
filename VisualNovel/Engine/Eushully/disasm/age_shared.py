import struct
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass
class BinaryHeader:
    signature: bytes  # 8 bytes
    local_integer_1: int
    local_floats: int
    local_strings_1: int
    local_integer_2: int
    unknown_data: int
    local_strings_2: int
    sub_header_length: int
    table_1_length: int
    table_1_offset: int
    table_2_length: int
    table_2_offset: int
    table_3_length: int
    table_3_offset: int


class Header:
    def __init__(self, fd: BinaryIO = None, binary_header: BinaryHeader = None):
        if fd:
            sig = fd.read(4)
            if sig == b"SYS4":
                fd.seek(0)
                self._parse_sys4(fd)
            elif sig[:4] == b"S\x00Y\x00":  # UTF-16LE "SYS5"
                fd.seek(0)
                self._parse_sys5(fd)
            else:
                raise ValueError(f"Unknown signature: {sig}")
        elif binary_header:
            self.header = binary_header
            if self.header.signature[3:4] == b"5":
                self.is_ver5 = True
                self.length = 0x44
            elif self.header.signature[3:4] == b"4":
                self.is_ver5 = False
                self.length = 0x3C
            else:
                raise ValueError(f"Unknown header version: {self.header.signature}")

    def _parse_sys4(self, fd: BinaryIO):
        self.is_ver5 = False
        self.length = 0x3C
        data = fd.read(self.length)
        unpacked = struct.unpack("<8s13I", data)
        self.header = BinaryHeader(*unpacked)

    def _parse_sys5(self, fd: BinaryIO):
        self.is_ver5 = True
        self.length = 0x44
        sig = fd.read(16)  # UTF-16LE "SYS5501 " + null padding
        data = fd.read(self.length - 8)
        unpacked = struct.unpack("<13I", data)
        self.header = BinaryHeader(sig[:8].decode("utf-16le").encode("utf-8"), *unpacked)


@dataclass
class Argument:
    arg_type: int = 0
    raw_data: int = 0
    decoded_string: str = ""
    data_array: list[int] = field(default_factory=list)


@dataclass
class InstructionDef:
    op_code: int
    label: str
    arg_count: int


class Instruction:
    def __init__(self, definition: InstructionDef, offset: int, arguments: list[Argument] = None):
        self.definition = definition
        self.offset = offset
        self.arguments = arguments if arguments else []


def cp932_to_utf8(data: bytes) -> str:
    try:
        return data.decode("cp932")
    except Exception:
        return data.decode("cp932", errors="replace")


def utf8_to_cp932(text: str) -> bytes:
    return text.encode("cp932", errors="replace")


def utf16le_to_utf8(data: bytes) -> str:
    return data.decode("utf-16le", errors="replace")


def utf8_to_utf16le(text: str) -> bytes:
    return text.encode("utf-16le")


def get_type_label(arg_type: int) -> str:
    type_map = {
        0: "",
        1: "float",
        2: "",
        3: "global-int",
        4: "global-float",
        5: "global-string",
        6: "global-ptr",
        8: "global-string-ptr",
        9: "local-int",
        0xA: "local-float",
        0xB: "local-string",
        0xC: "local-ptr",
        0xD: "local-float-ptr",
        0xE: "local-string-ptr",
        0x8003: "0x8003",
        0x8005: "0x8005",
        0x8009: "0x8009",
        0x800B: "0x800B",
    }
    if arg_type not in type_map:
        raise ValueError(f"Unknown type value: 0x{arg_type:x}")
    return type_map[arg_type]


def get_type_from_label(label: str) -> int:
    type_map = {
        "local-int": 9,
        "local-ptr": 0xC,
        "global-int": 3,
        "global-float": 4,
        "global-string": 5,
        "global-ptr": 6,
        "global-string-ptr": 8,
        "local-float": 0xA,
        "local-string": 0xB,
        "local-string-ptr": 0xE,
        "float": 1,
        "local-float-ptr": 0xD,
        "0x8003": 0x8003,
        "0x8005": 0x8005,
        "0x8009": 0x8009,
        "0x800B": 0x800B,
    }
    if label not in type_map:
        raise ValueError(f"Unknown variable type: {label}")
    return type_map[label]


def is_control_flow(instruction: Instruction | InstructionDef) -> bool:
    if isinstance(instruction, Instruction):
        op_code = instruction.definition.op_code
    else:
        op_code = instruction.op_code
    return op_code in {0x8C, 0x8F, 0xA0, 0xCC, 0xFB, 0xD4, 0x90, 0x7B}


def is_label_argument(instruction: Instruction, idx: int) -> bool:
    op = instruction.definition.op_code
    if idx >= len(instruction.arguments):
        return False
    raw = instruction.arguments[idx].raw_data

    if (op in {0x8C, 0x8F}) and raw != 0xFFFFFFFF:
        return True
    if op == 0xA0 and idx > 0 and raw != 0xFFFFFFFF:
        return True
    if op in {0xCC, 0xFB} and idx > 0 and raw != 0xFFFFFFFF:
        return True
    if op == 0xD4 and idx >= 2 and raw != 0xFFFFFFFF:
        return True
    if op == 0x90 and idx >= 4 and raw != 0xFFFFFFFF:
        return True
    if op == 0x7B and raw != 0xFFFFFFFF:
        return True
    return False


def compute_instruction_length(definition: InstructionDef) -> int:
    return 4 + (definition.arg_count * 8)
