from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional


class CommandType(IntEnum):
    JMP = 0x0
    JNZ = 0x1
    JZ = 0x2
    CALL_UINT_ID = 0x3
    CALL_BYTE_ID = 0x4
    MASK_VEIP = 0x5
    PUSH_R32 = 0x6
    POP_R32 = 0x7
    PUSH_INT32 = 0x8
    PUSH_STR_BYTE = 0x9
    PUSH_STR_SHORT = 0xA
    NONE = 0xB
    PUSH_STR_INT = 0xC
    PUSH_UINT32 = 0xD
    POP = 0xE
    PUSH_0 = 0xF
    UNKNOWN_1 = 0x10
    PUSH_0x = 0x11
    PUSH_SP = 0x12
    NEG = 0x13
    ADD = 0x14
    SUB = 0x15
    MUL = 0x16
    DIV = 0x17
    MOD = 0x18
    AND = 0x19
    OR = 0x1A
    XOR = 0x1B
    NOT = 0x1C
    BOOL1 = 0x1D
    BOOL2 = 0x1E
    BOOL3 = 0x1F
    BOOL4 = 0x20
    ISL = 0x21
    ISLE = 0x22
    ISNLE = 0x23
    ISNL = 0x24
    ISEQ = 0x25
    ISNEQ = 0x26
    SHL = 0x27
    SAR = 0x28
    INC = 0x29
    DEC = 0x2A
    ADD_REG = 0x2B
    DEBUG = 0x2C
    CALL_UINT_NO_PARAM = 0x2D
    ADD_2 = 0x2E
    FPCOPY = 0x2F
    FPGET = 0x30
    INITSTACK = 0x31
    Unknown2 = 0x32
    RET = 0x33


class StringTag(IntEnum):
    NONE = 0
    NAME = 1
    LABEL = 2
    CHAPTER = 3
    SELECT = 4


@dataclass
class VarItem:
    name: str
    parameters: List[int] = field(default_factory=list)


@dataclass
class FunctionItem:
    name: str
    id: int
    reserved0: int
    vm_code_offset: int
    command: Optional["BaseCommand"] = None


@dataclass
class LabelItem:
    name: str
    vm_code_offset: int
    command: Optional["BaseCommand"] = None


@dataclass
class StringItem:
    text: str
    offset: int
    tag: StringTag = StringTag.NONE

    def escape(self) -> str:
        if not self.text:
            return "[EMPTY]"
        if self.text == "　":
            return "[EMPTY_LINE]"

        result = self.text
        result = result.replace("\t", "\\t")
        result = result.replace("\r", "\\r")
        result = result.replace("\a", "\\a")
        result = result.replace("\b", "\\b")
        result = result.replace("\n", "\\n")
        result = result.replace("\x00", "\\0")
        result = result.replace("\x01", "\\1")
        result = result.replace("\x02", "\\2")
        result = result.replace("\x03", "\\3")
        result = result.replace("\x04", "\\4")
        result = result.replace("\x05", "\\5")
        result = result.replace("\x06", "\\6")
        return result

    def unescape(self) -> str:
        if self.text == "[EMPTY]":
            return ""
        if self.text == "[EMPTY_LINE]":
            return "　"

        result = self.text
        result = result.replace("\\t", "\t")
        result = result.replace("\\r", "\r")
        result = result.replace("\\a", "\a")
        result = result.replace("\\b", "\b")
        result = result.replace("\\n", "\n")
        result = result.replace("\\0", "\x00")
        result = result.replace("\\1", "\x01")
        result = result.replace("\\2", "\x02")
        result = result.replace("\\3", "\x03")
        result = result.replace("\\4", "\x04")
        result = result.replace("\\5", "\x05")
        result = result.replace("\\6", "\x06")
        return result

    def dump(self) -> str:
        return self.unescape()


@dataclass
class LineItem:
    voice: Optional[str] = None
    texts: List[StringItem] = field(default_factory=list)
    end: str = ""

    @property
    def text(self) -> str:
        return "\n".join(item.text for item in self.texts)

    def dump(self) -> str:
        voice_path = f"\a\b{self.voice}\x00" if self.voice else ""
        text_content = "\n".join(item.dump().replace("[NAME]", "\a\f\x01\x00") for item in self.texts)
        return voice_path + text_content + self.end


@dataclass
class ChapterStringConfig:
    name: str = ""
    index: int = 0


@dataclass
class ChapterString:
    name: str
    line: LineItem


@dataclass
class Chapter:
    title: str
    strings: List[ChapterString]
    start: int
    end: int


# Command classes
@dataclass
class BaseCommand:
    offset: int = 0

    @property
    def type(self) -> CommandType:
        raise NotImplementedError

    @property
    def length(self) -> int:
        return 1  # Just the opcode byte


@dataclass
class NoArgumentCommand(BaseCommand):
    command_type: CommandType = CommandType.NONE

    @property
    def type(self) -> CommandType:
        return self.command_type


@dataclass
class ByteArgumentCommand(BaseCommand):
    command_type: CommandType = CommandType.NONE
    argument: int = 0

    @property
    def type(self) -> CommandType:
        return self.command_type

    @property
    def length(self) -> int:
        return 2  # opcode + 1 byte


@dataclass
class UIntArgumentCommand(BaseCommand):
    command_type: CommandType = CommandType.NONE
    argument: int = 0

    @property
    def type(self) -> CommandType:
        return self.command_type

    @property
    def length(self) -> int:
        return 5  # opcode + 4 bytes


@dataclass
class JmpCommand(BaseCommand):
    command_type: CommandType = CommandType.JMP
    target_offset: int = 0
    target_command: Optional[BaseCommand] = None

    @property
    def type(self) -> CommandType:
        return self.command_type

    @property
    def length(self) -> int:
        return 5  # opcode + 4 bytes

    @property
    def command_offset(self) -> int:
        return self.target_offset & 0xFFFFFF


@dataclass
class CallCommand(BaseCommand):
    command_type: CommandType = CommandType.CALL_UINT_NO_PARAM
    function: Optional[FunctionItem] = None
    parameter: Optional[int] = None

    @property
    def type(self) -> CommandType:
        return self.command_type

    @property
    def length(self) -> int:
        if self.command_type == CommandType.CALL_UINT_ID:
            return 6  # opcode + 4 bytes + 1 byte
        elif self.command_type == CommandType.CALL_BYTE_ID:
            return 3  # opcode + 1 byte + 1 byte
        elif self.command_type == CommandType.CALL_UINT_NO_PARAM:
            return 5  # opcode + 4 bytes
        return 1


@dataclass
class PushStringCommand(BaseCommand):
    command_type: CommandType = CommandType.PUSH_STR_INT
    string_item: Optional[StringItem] = None

    @property
    def type(self) -> CommandType:
        return self.command_type

    @property
    def length(self) -> int:
        if self.command_type == CommandType.PUSH_STR_BYTE:
            return 2  # opcode + 1 byte
        elif self.command_type == CommandType.PUSH_STR_SHORT:
            return 3  # opcode + 2 bytes
        elif self.command_type == CommandType.PUSH_STR_INT:
            return 5  # opcode + 4 bytes
        return 1
