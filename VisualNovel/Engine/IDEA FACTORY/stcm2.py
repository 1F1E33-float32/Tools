# Reference: https://github.com/robbie01/stcm2-asm

import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

STCM2_MAGIC = b"STCM2"
STCM2_TAG_LENGTH = 32 - len(STCM2_MAGIC)
GLOBAL_DATA_MAGIC = b"GLOBAL_DATA\x00"
CODE_START_MAGIC = b"CODE_START_\x00"
EXPORT_DATA_MAGIC = b"EXPORT_DATA\x00"


class Buffer:
    def __init__(self, data: bytes, offset: int = 0):
        self._data = data
        self.offset = offset

    def startswith(self, prefix: bytes) -> bool:
        return self._data[self.offset :].startswith(prefix)

    def advance(self, n: int) -> None:
        self.offset += n

    def get_u32_le(self) -> int:
        (v,) = struct.unpack_from("<I", self._data, self.offset)
        self.offset += 4
        return v

    def split_to(self, n: int) -> bytes:
        start = self.offset
        end = start + n
        chunk = self._data[start:end]
        self.offset = end
        return chunk

    def __getitem__(self, slc):
        return self._data[self.offset :][slc]

    def __len__(self) -> int:
        return len(self._data) - self.offset


class ParameterKind:
    ACTION_REF = "ActionRef"
    DATA_POINTER = "DataPointer"
    VALUE = "Value"
    GLOBAL_DATA_POINTER = "GlobalDataPointer"


@dataclass
class Parameter:
    kind: str
    value: int

    @staticmethod
    def action_ref(addr: int) -> "Parameter":
        return Parameter(ParameterKind.ACTION_REF, addr)

    @staticmethod
    def data_pointer(offset: int) -> "Parameter":
        return Parameter(ParameterKind.DATA_POINTER, offset)

    @staticmethod
    def value(v: int) -> "Parameter":
        return Parameter(ParameterKind.VALUE, v)

    @staticmethod
    def global_data_pointer(offset: int) -> "Parameter":
        return Parameter(ParameterKind.GLOBAL_DATA_POINTER, offset)

    @staticmethod
    def parse(triple: Tuple[int, int, int], data_addr: int, data_len: int, global_data_len: int) -> "Parameter":
        # In Rust patterns, `0x40000000 | 0xff000000` is an OR-pattern, i.e.,
        # it matches either 0x40000000 or 0xff000000. Mirror that here.
        def is_sentinel(v: int) -> bool:
            return v in (0x40000000, 0xFF000000)

        a, b, c = triple
        gdo = GLOBAL_DATA_OFFSET
        # Follow Rust match arms exactly
        if a == 0xFFFFFF41 and is_sentinel(c):
            # [0xffffff41, addr, SENT]
            return Parameter.action_ref(b)
        if is_sentinel(b) and is_sentinel(c) and data_addr <= a < data_addr + data_len:
            return Parameter.data_pointer(a - data_addr)
        if is_sentinel(b) and is_sentinel(c) and gdo <= a < gdo + global_data_len:
            return Parameter.global_data_pointer(a - gdo)
        if is_sentinel(b) and is_sentinel(c):
            return Parameter.value(a)
        raise ValueError(f"bad parameter: {[a, b, c]!r}")


@dataclass
class Action:
    export: Optional[bytes]
    call: bool
    opcode: int
    params: List[Parameter]
    data: bytes

    def label(self, junk: bool) -> Optional[bytes]:
        if self.export is None:
            return None
        b = self.export
        if junk:
            # strip all trailing zeros
            i = len(b)
            while i > 0 and b[i - 1] == 0:
                i -= 1
            return b[:i]
        else:
            try:
                pos = b.index(0)
            except ValueError:
                pos = len(b)
            return b[:pos]

    def length(self) -> int:
        return 16 + 12 * len(self.params) + len(self.data)


@dataclass
class Stcm2:
    tag: bytes
    global_data: bytes
    actions: Dict[int, Action] = field(default_factory=dict)


def from_bytes(file_bytes: bytes) -> Stcm2:
    file = Buffer(file_bytes)
    start_offset = 0
    get_pos = lambda buf: buf.offset - start_offset

    if not file.startswith(STCM2_MAGIC):
        raise ValueError("Missing STCM2 magic")
    file.advance(len(STCM2_MAGIC))
    tag = file.split_to(STCM2_TAG_LENGTH)
    export_addr = file.get_u32_le()
    export_len = file.get_u32_le()
    _unk1 = file.get_u32_le()
    _collection_addr = file.get_u32_le()
    _unk = file.split_to(32)
    if not file.startswith(GLOBAL_DATA_MAGIC):
        raise ValueError("Missing GLOBAL_DATA magic")
    file.advance(len(GLOBAL_DATA_MAGIC))
    # Compute and validate GLOBAL_DATA offset
    if get_pos(file) != GLOBAL_DATA_OFFSET:
        raise ValueError("GLOBAL_DATA offset mismatch")
    global_len = 0
    # Scan 4-byte aligned until CODE_START
    while not file[global_len:].startswith(CODE_START_MAGIC):
        global_len += 4
        if global_len + len(CODE_START_MAGIC) > len(file):
            raise ValueError("CODE_START magic not found")
    global_data = file.split_to(global_len)
    if not file.startswith(CODE_START_MAGIC):
        raise ValueError("Missing CODE_START magic")
    file.advance(len(CODE_START_MAGIC))

    actions: Dict[int, Action] = {}

    while get_pos(file) < int(export_addr) - len(EXPORT_DATA_MAGIC):
        addr = get_pos(file)

        global_call = file.get_u32_le()
        opcode = file.get_u32_le()
        nparams = file.get_u32_le()
        length = file.get_u32_le()

        if global_call == 0:
            call = False
        elif global_call == 1:
            call = True
        else:
            raise ValueError(f"global_call = {global_call:08X}")

        params: List[Parameter] = []
        for _ in range(nparams):
            a = file.get_u32_le()
            b = file.get_u32_le()
            c = file.get_u32_le()
            params.append(
                Parameter.parse(
                    (a, b, c),
                    addr + 16 + 12 * nparams,
                    length - 16 - 12 * nparams,
                    int(global_len),
                )
            )

        ndata = length - 16 - 12 * nparams
        data = file.split_to(ndata)

        if addr in actions:
            raise ValueError("duplicate action address")
        actions[addr] = Action(export=None, call=call, opcode=opcode, params=params, data=data)

    if not file.startswith(EXPORT_DATA_MAGIC):
        raise ValueError("Missing EXPORT_DATA magic")
    file.advance(len(EXPORT_DATA_MAGIC))

    for _ in range(export_len):
        if file.get_u32_le() != 0:
            raise ValueError("export padding was not zero")
        export = file.split_to(32)
        addr = file.get_u32_le()
        act = actions.get(addr)
        if act is None:
            raise ValueError("export does not match known action")
        if act.export is not None:
            raise ValueError("duplicate export for action")
        act.export = export

    return Stcm2(tag=tag, global_data=global_data, actions=actions)


# Derived constant after parser is loaded
GLOBAL_DATA_OFFSET = len(STCM2_MAGIC) + STCM2_TAG_LENGTH + 12 * 4 + len(GLOBAL_DATA_MAGIC)
