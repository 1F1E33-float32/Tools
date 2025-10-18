import struct
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple, Union

LUA51 = 0x51
LUA52 = 0x52
LUA53 = 0x53
LUA54 = 0x54
LUAJ1 = 0x11
LUAJ2 = 0x12


class LuaParseError(Exception):
    """Raised when a Lua bytecode stream cannot be decoded."""


@dataclass(frozen=True)
class LuaVersion:
    value: int

    def __str__(self) -> str:
        if self.value == LUAJ1:
            return "luajit1"
        if self.value == LUAJ2:
            return "luajit2"
        return f"lua{self.value:02x}"

    def is_luajit(self) -> bool:
        return self.value in (LUAJ1, LUAJ2)


@dataclass
class LuaHeader:
    lua_version: int
    format_version: int
    big_endian: bool
    int_size: int
    size_t_size: int
    instruction_size: int
    number_size: int
    number_integral: bool
    lj_flags: int = 0

    @property
    def version(self) -> LuaVersion:
        return LuaVersion(self.lua_version)


@dataclass
class LuaNumber:
    value: Union[int, float]
    is_integer: bool

    def __repr__(self) -> str:
        if self.is_integer:
            return f"Integer({self.value})"
        return f"Float({self.value})"


@dataclass
class LuaConstant:
    kind: str
    value: Any

    @classmethod
    def null(cls) -> "LuaConstant":
        return cls("null", None)

    @classmethod
    def bool(cls, value: bool) -> "LuaConstant":
        return cls("bool", bool(value))

    @classmethod
    def number(cls, value: LuaNumber) -> "LuaConstant":
        return cls("number", value)

    @classmethod
    def string(cls, data: bytes) -> "LuaConstant":
        return cls("string", data)

    def __repr__(self) -> str:
        if self.kind == "null":
            return "Null"
        if self.kind == "bool":
            return f"Bool({self.value})"
        if self.kind == "number":
            return f"Number({self.value!r})"
        if self.kind == "string":
            try:
                text = self.value.decode("utf-8")
            except UnicodeDecodeError:
                text = self.value.hex()
                return f"String(0x{text})"
            escaped = text.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace('"', '\\"')
            return f'String("{escaped}")'
        return f"{self.kind.capitalize()}({self.value})"


@dataclass
class LuaLocal:
    name: str
    start_pc: int
    end_pc: int
    reg: int = 0


@dataclass
class LuaVarArgInfo:
    has_arg: bool
    needs_arg: bool


@dataclass
class UpValue:
    on_stack: bool
    id: int
    kind: int = 0


@dataclass
class LuaChunk:
    name: bytes = b""
    line_defined: int = 0
    last_line_defined: int = 0
    num_upvalues: int = 0
    num_params: int = 0
    max_stack: int = 0
    flags: int = 0
    is_vararg: Optional[LuaVarArgInfo] = None
    instructions: List[int] = field(default_factory=list)
    constants: List[LuaConstant] = field(default_factory=list)
    num_constants: List[LuaNumber] = field(default_factory=list)
    prototypes: List["LuaChunk"] = field(default_factory=list)
    source_lines: List[Tuple[int, int]] = field(default_factory=list)
    locals: List[LuaLocal] = field(default_factory=list)
    upvalue_infos: List[UpValue] = field(default_factory=list)
    upvalue_names: List[bytes] = field(default_factory=list)
    lineinfo: List[int] = field(default_factory=list)
    abslineinfo: List[int] = field(default_factory=list)
    linegaplog: int = 0

    def display_name(self) -> str:
        return self.name.decode("utf-8", errors="replace")

    def is_empty(self) -> bool:
        return not self.instructions


@dataclass
class LuaBytecode:
    header: LuaHeader
    main_chunk: LuaChunk


class ByteReader:
    def __init__(self, data: bytes):
        self._data = memoryview(data)
        self._pos = 0

    def tell(self) -> int:
        return self._pos

    def remaining(self) -> int:
        return len(self._data) - self._pos

    def read(self, length: int) -> bytes:
        if length < 0:
            raise LuaParseError("negative read length")
        if self._pos + length > len(self._data):
            raise LuaParseError("unexpected end of data")
        out = self._data[self._pos : self._pos + length].tobytes()
        self._pos += length
        return out

    def read_u8(self) -> int:
        return self._read_int_struct("<B")

    def read_uint(self, size: int, big_endian: bool) -> int:
        fmt = self._fmt(size, big_endian, unsigned=True)
        return self._read_int_struct(fmt)

    def read_int(self, size: int, big_endian: bool) -> int:
        fmt = self._fmt(size, big_endian, unsigned=False)
        return self._read_int_struct(fmt)

    def read_float(self, size: int, big_endian: bool) -> float:
        if size == 4:
            fmt = ">" if big_endian else "<"
            return self._read_float_struct(f"{fmt}f")
        if size == 8:
            fmt = ">" if big_endian else "<"
            return self._read_float_struct(f"{fmt}d")
        raise LuaParseError(f"unsupported float size {size}")

    def _fmt(self, size: int, big_endian: bool, unsigned: bool) -> str:
        mapping_unsigned = {1: "B", 2: "H", 4: "I", 8: "Q"}
        mapping_signed = {1: "b", 2: "h", 4: "i", 8: "q"}
        mapping = mapping_unsigned if unsigned else mapping_signed
        if size not in mapping:
            raise LuaParseError(f"unsupported integer size {size}")
        prefix = ">" if big_endian else "<"
        return f"{prefix}{mapping[size]}"

    def _read_int_struct(self, fmt: str) -> int:
        size = struct.calcsize(fmt)
        data = self.read(size)
        return struct.unpack(fmt, data)[0]

    def _read_float_struct(self, fmt: str) -> float:
        size = struct.calcsize(fmt)
        data = self.read(size)
        return struct.unpack(fmt, data)[0]


def parse_lua_bytecode(data: bytes) -> LuaBytecode:
    reader = ByteReader(data)
    header = _parse_header(reader)
    version = header.version
    if version.value == LUA51:
        chunk = _parse_chunk51(reader, header)
    elif version.value == LUA52:
        chunk = _parse_chunk52(reader, header)
    elif version.value == LUA53:
        chunk = _parse_chunk53(reader, header)
    elif version.value == LUA54:
        chunk = _parse_chunk54(reader, header)
    elif version.is_luajit():
        raise LuaParseError("LuaJIT bytecode is not supported in the Python port yet")
    else:
        raise LuaParseError(f"unsupported lua version 0x{version.value:02x}")
    return LuaBytecode(header=header, main_chunk=chunk)


def _parse_header(reader: ByteReader) -> LuaHeader:
    magic = reader.read(4)
    if magic == b"\x1bLua":
        version_byte = reader.read_u8()
        if version_byte == LUA51:
            format_version = reader.read_u8()
            endian_flag = reader.read_u8()
            int_size = reader.read_u8()
            size_t_size = reader.read_u8()
            instruction_size = reader.read_u8()
            number_size = reader.read_u8()
            number_integral = reader.read_u8()
            return LuaHeader(
                lua_version=LUA51,
                format_version=format_version,
                big_endian=endian_flag != 1,
                int_size=int_size,
                size_t_size=size_t_size,
                instruction_size=instruction_size,
                number_size=number_size,
                number_integral=number_integral != 0,
            )
        if version_byte == LUA52:
            format_version = reader.read_u8()
            endian_flag = reader.read_u8()
            int_size = reader.read_u8()
            size_t_size = reader.read_u8()
            instruction_size = reader.read_u8()
            number_size = reader.read_u8()
            number_integral = reader.read_u8()
            _luac_data = reader.read(6)
            return LuaHeader(
                lua_version=LUA52,
                format_version=format_version,
                big_endian=endian_flag != 1,
                int_size=int_size,
                size_t_size=size_t_size,
                instruction_size=instruction_size,
                number_size=number_size,
                number_integral=number_integral != 0,
            )
        if version_byte == LUA53:
            format_version = reader.read_u8()
            _luac_data = reader.read(6)
            int_size = reader.read_u8()
            size_t_size = reader.read_u8()
            instruction_size = reader.read_u8()
            _integer_size = reader.read_u8()
            number_size = reader.read_u8()
            _check_int = reader.read_int(8, big_endian=False)
            _check_num = reader.read_float(8, big_endian=False)
            _reserved = reader.read_u8()
            return LuaHeader(
                lua_version=LUA53,
                format_version=format_version,
                big_endian=sys.byteorder == "big",
                int_size=int_size,
                size_t_size=size_t_size,
                instruction_size=instruction_size,
                number_size=number_size,
                number_integral=False,
            )
        if version_byte == LUA54:
            format_version = reader.read_u8()
            _luac_data = reader.read(6)
            instruction_size = reader.read_u8()
            _integer_size = reader.read_u8()
            number_size = reader.read_u8()
            _check_int = reader.read_int(8, big_endian=False)
            _check_num = reader.read_float(8, big_endian=False)
            _reserved = reader.read_u8()
            return LuaHeader(
                lua_version=LUA54,
                format_version=format_version,
                big_endian=sys.byteorder == "big",
                int_size=4,
                size_t_size=8,
                instruction_size=instruction_size,
                number_size=number_size,
                number_integral=False,
            )
        raise LuaParseError(f"unknown Lua bytecode version 0x{version_byte:02x}")
    if magic == b"\x1bLJ":
        version_byte = reader.read_u8()
        lj_flags = reader.read_u8()
        if version_byte == 0x01:
            return LuaHeader(
                lua_version=LUAJ1,
                format_version=0,
                big_endian=(lj_flags & 0x01) != 0,
                int_size=4,
                size_t_size=4,
                instruction_size=4,
                number_size=4,
                number_integral=False,
                lj_flags=lj_flags,
            )
        if version_byte == 0x02:
            return LuaHeader(
                lua_version=LUAJ2,
                format_version=0,
                big_endian=(lj_flags & 0x01) != 0,
                int_size=4,
                size_t_size=4,
                instruction_size=4,
                number_size=4,
                number_integral=False,
                lj_flags=lj_flags,
            )
        raise LuaParseError(f"unsupported LuaJIT version byte 0x{version_byte:02x}")
    raise LuaParseError("input is not a Lua bytecode chunk")


def _read_lua_int(reader: ByteReader, header: LuaHeader) -> int:
    size = header.int_size
    if size == 0:
        raise LuaParseError("invalid integer size 0")
    if size == 1:
        return reader.read_u8()
    return reader.read_uint(size, header.big_endian)


def _read_lua_size_t(reader: ByteReader, header: LuaHeader) -> int:
    size = header.size_t_size
    if size == 0:
        raise LuaParseError("invalid size_t size 0")
    if size == 1:
        return reader.read_u8()
    return reader.read_uint(size, header.big_endian)


def _read_lua_number(reader: ByteReader, header: LuaHeader) -> LuaNumber:
    if header.number_integral:
        size = header.number_size
        value = reader.read_int(size, header.big_endian)
        return LuaNumber(value=value, is_integer=True)
    size = header.number_size
    value = reader.read_float(size, header.big_endian)
    return LuaNumber(value=value, is_integer=False)


def _read_lua_string(reader: ByteReader, header: LuaHeader) -> bytes:
    length = _read_lua_size_t(reader, header)
    if length == 0:
        return b""
    data = reader.read(length)
    if data and data[-1] == 0:
        return data[:-1]
    return data


def _read_local51(reader: ByteReader, header: LuaHeader) -> LuaLocal:
    name = _read_lua_string(reader, header)
    start_pc = _read_lua_int(reader, header)
    end_pc = _read_lua_int(reader, header)
    return LuaLocal(name=name.decode("utf-8", errors="replace"), start_pc=start_pc, end_pc=end_pc)


def _read_constant_basic(reader: ByteReader, header: LuaHeader) -> LuaConstant:
    tag = reader.read_u8()
    if tag == 0:
        return LuaConstant.null()
    if tag == 1:
        value = reader.read_u8()
        return LuaConstant.bool(value != 0)
    if tag == 3:
        number = _read_lua_number(reader, header)
        return LuaConstant.number(number)
    if tag == 4:
        data = _read_lua_string(reader, header)
        return LuaConstant.string(data)
    raise LuaParseError(f"unsupported constant tag {tag}")


def _parse_chunk51(reader: ByteReader, header: LuaHeader) -> LuaChunk:
    name = _read_lua_string(reader, header)
    line_defined = _read_lua_int(reader, header)
    last_line_defined = _read_lua_int(reader, header)
    num_upvalues = reader.read_u8()
    num_params = reader.read_u8()
    is_vararg_flag = reader.read_u8()
    max_stack = reader.read_u8()

    instructions = _read_instructions(reader, header)
    constants = _read_constants_basic(reader, header)
    prototypes = _read_prototypes(reader, header, _parse_chunk51)
    source_lines = _read_source_lines(reader, header)
    locals_ = _read_locals(reader, header, _read_local51)
    upvalue_names = _read_upvalue_names(reader, header)

    chunk = LuaChunk(
        name=name,
        line_defined=line_defined,
        last_line_defined=last_line_defined,
        num_upvalues=num_upvalues,
        num_params=num_params,
        max_stack=max_stack,
        instructions=instructions,
        constants=constants,
        prototypes=prototypes,
        source_lines=source_lines,
        locals=locals_,
        upvalue_names=upvalue_names,
    )
    if is_vararg_flag & 0x02:
        chunk.is_vararg = LuaVarArgInfo(
            has_arg=(is_vararg_flag & 0x01) != 0,
            needs_arg=(is_vararg_flag & 0x04) != 0,
        )
    return chunk


def _parse_chunk52(reader: ByteReader, header: LuaHeader) -> LuaChunk:
    line_defined = _read_lua_int(reader, header)
    last_line_defined = _read_lua_int(reader, header)
    num_params = reader.read_u8()
    is_vararg_flag = reader.read_u8()
    max_stack = reader.read_u8()

    instructions = _read_instructions(reader, header)
    constants = _read_constants_basic(reader, header)
    prototypes = _read_prototypes(reader, header, _parse_chunk52)
    upvalues = _read_upvalues52(reader, header)
    name = _read_lua_string(reader, header)
    source_lines = _read_source_lines(reader, header)
    locals_ = _read_locals(reader, header, _read_local51)
    upvalue_names = _read_upvalue_names(reader, header)

    chunk = LuaChunk(
        name=name,
        line_defined=line_defined,
        last_line_defined=last_line_defined,
        num_upvalues=len(upvalues),
        num_params=num_params,
        max_stack=max_stack,
        instructions=instructions,
        constants=constants,
        prototypes=prototypes,
        source_lines=source_lines,
        locals=locals_,
        upvalue_infos=upvalues,
        upvalue_names=upvalue_names,
    )
    if is_vararg_flag:
        chunk.is_vararg = LuaVarArgInfo(has_arg=True, needs_arg=True)
    return chunk


def _parse_chunk53(reader: ByteReader, header: LuaHeader) -> LuaChunk:
    name = _read_lua53_string(reader)
    line_defined = _read_lua_int(reader, header)
    last_line_defined = _read_lua_int(reader, header)
    num_params = reader.read_u8()
    is_vararg_flag = reader.read_u8()
    max_stack = reader.read_u8()

    instructions = _read_instructions(reader, header)
    constants = _read_constants53(reader, header)
    upvalues = _read_upvalues52(reader, header)
    prototypes = _read_prototypes(reader, header, _parse_chunk53)
    source_lines = _read_source_lines(reader, header)
    locals_ = _read_locals(reader, header, _read_local53)
    upvalue_names = _read_upvalue_names53(reader, header)

    chunk = LuaChunk(
        name=name,
        line_defined=line_defined,
        last_line_defined=last_line_defined,
        num_upvalues=len(upvalues),
        num_params=num_params,
        max_stack=max_stack,
        instructions=instructions,
        constants=constants,
        upvalue_infos=upvalues,
        prototypes=prototypes,
        source_lines=source_lines,
        locals=locals_,
        upvalue_names=upvalue_names,
    )
    if is_vararg_flag:
        chunk.is_vararg = LuaVarArgInfo(has_arg=True, needs_arg=True)
    return chunk


def _parse_chunk54(reader: ByteReader, header: LuaHeader) -> LuaChunk:
    name = _read_lua54_string(reader)
    line_defined = _read_lua54_int(reader)
    last_line_defined = _read_lua54_int(reader)
    num_params = reader.read_u8()
    is_vararg_flag = reader.read_u8()
    max_stack = reader.read_u8()

    instruction_count = _read_lua54_int(reader)
    instructions = [reader.read_uint(header.instruction_size, header.big_endian) for _ in range(instruction_count)]
    constants = _read_constants54(reader)
    upvalues = _read_upvalues54(reader)
    prototypes = _read_prototypes54(reader, header)
    line_info = _read_lua54_lineinfo(reader)
    source_lines = _read_lua54_source_lines(reader)
    locals_ = _read_locals54(reader)
    upvalue_names = _read_lua54_upvalue_names(reader)

    chunk = LuaChunk(
        name=name,
        line_defined=line_defined,
        last_line_defined=last_line_defined,
        num_upvalues=len(upvalues),
        num_params=num_params,
        max_stack=max_stack,
        instructions=instructions,
        constants=constants,
        upvalue_infos=upvalues,
        prototypes=prototypes,
        source_lines=source_lines,
        locals=locals_,
        upvalue_names=upvalue_names,
        lineinfo=line_info,
    )
    if is_vararg_flag:
        chunk.is_vararg = LuaVarArgInfo(has_arg=True, needs_arg=True)
    return chunk


def _read_instructions(reader: ByteReader, header: LuaHeader) -> List[int]:
    count = _read_lua_int(reader, header)
    if header.instruction_size != 4:
        raise LuaParseError("only 32-bit instructions are supported")
    instructions = []
    for _ in range(count):
        instructions.append(reader.read_uint(4, header.big_endian))
    return instructions


def _read_constants_basic(reader: ByteReader, header: LuaHeader) -> List[LuaConstant]:
    count = _read_lua_int(reader, header)
    return [_read_constant_basic(reader, header) for _ in range(count)]


def _read_prototypes(
    reader: ByteReader,
    header: LuaHeader,
    parser,
) -> List[LuaChunk]:
    count = _read_lua_int(reader, header)
    prototypes = []
    for _ in range(count):
        prototypes.append(parser(reader, header))
    return prototypes


def _read_source_lines(reader: ByteReader, header: LuaHeader) -> List[Tuple[int, int]]:
    count = _read_lua_int(reader, header)
    lines = []
    for _ in range(count):
        line = _read_lua_int(reader, header)
        lines.append((int(line), 0))
    return lines


def _read_locals(reader: ByteReader, header: LuaHeader, factory) -> List[LuaLocal]:
    count = _read_lua_int(reader, header)
    locals_ = []
    for _ in range(count):
        locals_.append(factory(reader, header))
    return locals_


def _read_upvalue_names(reader: ByteReader, header: LuaHeader) -> List[bytes]:
    count = _read_lua_int(reader, header)
    names = []
    for _ in range(count):
        names.append(_read_lua_string(reader, header))
    return names


def _read_upvalues52(reader: ByteReader, header: LuaHeader) -> List[UpValue]:
    count = _read_lua_int(reader, header)
    result = []
    for _ in range(count):
        on_stack = reader.read_uint(1, False) != 0
        upvalue_id = reader.read_uint(1, False)
        result.append(UpValue(on_stack=on_stack, id=upvalue_id, kind=0))
    return result


def _read_lua53_string(reader: ByteReader) -> bytes:
    length = reader.read_u8()
    if length == 0:
        return b""
    if length == 0xFF:
        length = reader.read_uint(8, False)
    data = reader.read(length - 1)
    return data


def _read_local53(reader: ByteReader, header: LuaHeader) -> LuaLocal:
    name = _read_lua53_string(reader)
    start_pc = _read_lua_int(reader, header)
    end_pc = _read_lua_int(reader, header)
    return LuaLocal(name=name.decode("utf-8", errors="replace"), start_pc=start_pc, end_pc=end_pc)


def _read_upvalue_names53(reader: ByteReader, header: LuaHeader) -> List[bytes]:
    count = _read_lua_int(reader, header)
    names = []
    for _ in range(count):
        names.append(_read_lua53_string(reader))
    return names


def _read_constants53(reader: ByteReader, header: LuaHeader) -> List[LuaConstant]:
    count = _read_lua_int(reader, header)
    constants: List[LuaConstant] = []
    for _ in range(count):
        tag = reader.read_u8()
        if tag == 0x00:
            constants.append(LuaConstant.null())
        elif tag == 0x01:
            value = reader.read_u8()
            constants.append(LuaConstant.bool(value != 0))
        elif tag == 0x03:
            number = LuaNumber(value=reader.read_float(8, False), is_integer=False)
            constants.append(LuaConstant.number(number))
        elif tag in (0x04, 0x14):
            strlen = reader.read_u8()
            if strlen == 0:
                constants.append(LuaConstant.string(b""))
            else:
                data = reader.read(strlen - 1)
                constants.append(LuaConstant.string(data))
        elif tag == 0x13:
            value = reader.read_uint(8, False)
            constants.append(LuaConstant.number(LuaNumber(value=value, is_integer=True)))
        else:
            raise LuaParseError(f"unsupported Lua 5.3 constant tag 0x{tag:02x}")
    return constants


def _lua54_read_unsigned(reader: ByteReader, limit: int) -> int:
    x = 0
    limit >>= 7
    while True:
        b = reader.read_u8()
        if x >= limit:
            raise LuaParseError("integer overflow while decoding lua54 unsigned value")
        x = (x << 7) | (b & 0x7F)
        if b & 0x80:
            break
    return x


def _read_lua54_size(reader: ByteReader) -> int:
    return _lua54_read_unsigned(reader, sys.maxsize)


def _read_lua54_int(reader: ByteReader) -> int:
    return _lua54_read_unsigned(reader, (1 << 31) - 1)


def _read_lua54_string(reader: ByteReader) -> bytes:
    size = _read_lua54_size(reader)
    if size == 0:
        return b""
    data = reader.read(size - 1)
    return data


def _read_constants54(reader: ByteReader) -> List[LuaConstant]:
    count = _read_lua54_int(reader)
    result: List[LuaConstant] = []
    for _ in range(count):
        tag = reader.read_u8()
        if tag == 0x00:
            result.append(LuaConstant.null())
        elif tag == 0x01:
            result.append(LuaConstant.bool(False))
        elif tag == 0x11:
            result.append(LuaConstant.bool(True))
        elif tag == 0x13:
            value = reader.read_float(8, False)
            result.append(LuaConstant.number(LuaNumber(value=value, is_integer=False)))
        elif tag in (0x04, 0x14):
            data = _read_lua54_string(reader)
            result.append(LuaConstant.string(data))
        elif tag == 0x03:
            value = reader.read_uint(8, False)
            result.append(LuaConstant.number(LuaNumber(value=value, is_integer=True)))
        else:
            raise LuaParseError(f"unsupported Lua 5.4 constant tag 0x{tag:02x}")
    return result


def _read_upvalues54(reader: ByteReader) -> List[UpValue]:
    count = _read_lua54_int(reader)
    upvalues = []
    for _ in range(count):
        on_stack = reader.read_u8() != 0
        upvalue_id = reader.read_u8()
        kind = reader.read_u8()
        upvalues.append(UpValue(on_stack=on_stack, id=upvalue_id, kind=kind))
    return upvalues


def _read_prototypes54(reader: ByteReader, header: LuaHeader) -> List[LuaChunk]:
    count = _read_lua54_int(reader)
    protos = []
    for _ in range(count):
        protos.append(_parse_chunk54(reader, header))
    return protos


def _read_lua54_lineinfo(reader: ByteReader) -> List[int]:
    count = _read_lua54_int(reader)
    return [reader.read_u8() for _ in range(count)]


def _read_lua54_source_lines(reader: ByteReader) -> List[Tuple[int, int]]:
    count = _read_lua54_int(reader)
    lines: List[Tuple[int, int]] = []
    for _ in range(count):
        start = _read_lua54_int(reader)
        end = _read_lua54_int(reader)
        lines.append((start, end))
    return lines


def _read_locals54(reader: ByteReader) -> List[LuaLocal]:
    count = _read_lua54_int(reader)
    locals_: List[LuaLocal] = []
    for _ in range(count):
        name = _read_lua54_string(reader)
        start_pc = _read_lua54_int(reader)
        end_pc = _read_lua54_int(reader)
        locals_.append(LuaLocal(name=name.decode("utf-8", errors="replace"), start_pc=start_pc, end_pc=end_pc))
    return locals_


def _read_lua54_upvalue_names(reader: ByteReader) -> List[bytes]:
    count = _read_lua54_int(reader)
    names = []
    for _ in range(count):
        names.append(_read_lua54_string(reader))
    return names
