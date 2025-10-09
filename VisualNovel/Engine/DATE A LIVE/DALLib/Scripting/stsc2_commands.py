"""
Python translation of the STSC2 command helpers and DALRD command table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from DALLib.IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter
from DALLib.Scripting.stsc2_node import STSC2Node


class CommandArgType(Enum):
    NODE = "node"
    COMMAND_REF = "command_ref"
    BYTE = "byte"
    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    INT64 = "int64"
    UINT64 = "uint64"
    BOOL = "bool"
    FLOAT = "float"
    STRING = "string"
    UNKNOWN = "unknown"


def _read_value(reader: ExtendedBinaryReader, arg_type: CommandArgType) -> Any:
    if arg_type == CommandArgType.NODE:
        return STSC2Node().read(reader)
    if arg_type == CommandArgType.COMMAND_REF:
        return reader.read_uint32()
    if arg_type == CommandArgType.BOOL:
        return reader.read_bool()
    if arg_type == CommandArgType.BYTE:
        return reader.read_byte()
    if arg_type == CommandArgType.INT16:
        return reader.read_int16()
    if arg_type == CommandArgType.UINT16:
        return reader.read_uint16()
    if arg_type == CommandArgType.INT32:
        return reader.read_int32()
    if arg_type == CommandArgType.UINT32:
        return reader.read_uint32()
    if arg_type == CommandArgType.INT64:
        return reader.read_int64()
    if arg_type == CommandArgType.UINT64:
        return reader.read_uint64()
    if arg_type == CommandArgType.FLOAT:
        return reader.read_single()
    if arg_type == CommandArgType.STRING:
        return reader.read_string_elsewhere()
    return None


def _write_value(writer: ExtendedBinaryWriter, arg_type: CommandArgType, value: Any):
    if arg_type == CommandArgType.BOOL:
        writer.write_bool(bool(value))
    elif arg_type == CommandArgType.BYTE:
        writer.write_byte(int(value))
    elif arg_type == CommandArgType.INT16:
        writer.write_int16(int(value))
    elif arg_type == CommandArgType.UINT16:
        writer.write_uint16(int(value))
    elif arg_type == CommandArgType.INT32:
        writer.write_int32(int(value))
    elif arg_type == CommandArgType.UINT32:
        writer.write_uint32(int(value))
    elif arg_type == CommandArgType.INT64:
        writer.write_int64(int(value))
    elif arg_type == CommandArgType.UINT64:
        writer.write_uint64(int(value))
    elif arg_type == CommandArgType.FLOAT:
        writer.write_single(float(value))
    else:
        raise ValueError(f"Unsupported command argument type {arg_type}")


@dataclass
class Command:
    name: str
    argument_types: Optional[Sequence[CommandArgType]]
    arguments: List[Any] = field(default_factory=list)
    _cmd_line_info: bytes = b""

    def set_cmd_line_info(self, data: bytes):
        self._cmd_line_info = data

    def read(
        self, reader: ExtendedBinaryReader, cmd_line_info: Optional[bytes]
    ) -> "Command":
        line = Command(self.name, list(self.argument_types) if self.argument_types else None)
        line._cmd_line_info = cmd_line_info or b""

        if not self.argument_types:
            return line

        for arg_type in self.argument_types:
            if arg_type == CommandArgType.NODE:
                line.arguments.append(STSC2Node().read(reader))
            elif arg_type == CommandArgType.COMMAND_REF:
                line.arguments.append(reader.read_uint32())
            else:
                line.arguments.append(_read_value(reader, arg_type))

        return line

    def write(
        self,
        writer: ExtendedBinaryWriter,
        string_table: List[str],
        nodes: List[STSC2Node],
        commands: Sequence["Command"],
    ):
        if self._cmd_line_info:
            writer.write(self._cmd_line_info)

        opcode = next(
            index for index, template in enumerate(commands) if template.name == self.name
        )
        writer.write_byte(opcode)

        if not self.argument_types:
            return

        for index, arg in enumerate(self.arguments):
            arg_type = self.argument_types[index]
            if arg_type == CommandArgType.NODE:
                writer.add_offset(f"node{len(nodes)}")
                nodes.append(arg)
            elif arg_type == CommandArgType.COMMAND_REF:
                key = f"{id(self)}_{id(arg)}"
                writer.add_offset(key)
            elif arg_type == CommandArgType.STRING:
                writer.add_offset(f"str{len(string_table)}")
                string_table.append(arg if arg is not None else "")
            else:
                _write_value(writer, arg_type, arg)

    def name_lookup(self, commands: Sequence["Command"]) -> "Command":
        for template in commands:
            if template.name == self.name:
                return template
        raise ValueError(f"Command template for {self.name} not found")

    def __str__(self) -> str:
        return self.name


class CommandFuncCall(Command):
    def __init__(self):
        super().__init__("FuncCall", None)

    def read(
        self, reader: ExtendedBinaryReader, cmd_line_info: Optional[bytes]
    ) -> Command:
        reader.jump_ahead(0x04)
        param_count = reader.read_byte()
        reader.jump_behind(5)

        args: List[CommandArgType] = [
            CommandArgType.UINT32,
            CommandArgType.BYTE,
            CommandArgType.BYTE,
            CommandArgType.INT64,
        ]

        for _ in range(param_count):
            args.extend([CommandArgType.BYTE, CommandArgType.NODE])

        args.append(CommandArgType.COMMAND_REF)
        self.argument_types = args
        return super().read(reader, cmd_line_info)


class CommandReturn(Command):
    def __init__(self):
        super().__init__("Return", None)

    def read(
        self, reader: ExtendedBinaryReader, cmd_line_info: Optional[bytes]
    ) -> Command:
        param_type = reader.read_byte()
        reader.jump_behind(1)

        if param_type == 0:
            read_type = CommandArgType.INT32
        elif param_type == 1:
            read_type = CommandArgType.FLOAT
        elif param_type == 2:
            read_type = CommandArgType.BOOL
        elif param_type == 3:
            read_type = CommandArgType.STRING
        else:
            read_type = None

        if read_type is None:
            self.argument_types = [CommandArgType.BYTE]
        else:
            self.argument_types = [CommandArgType.BYTE, read_type]

        return super().read(reader, cmd_line_info)


class CommandJumpSwitch(Command):
    def __init__(self):
        super().__init__("JumpSwitch", None)

    def read(
        self, reader: ExtendedBinaryReader, cmd_line_info: Optional[bytes]
    ) -> Command:
        reader.jump_ahead(0x04)
        count = reader.read_uint16() & 0x7FF
        reader.jump_behind(6)

        args: List[CommandArgType] = [CommandArgType.NODE, CommandArgType.UINT16]
        for _ in range(count):
            args.extend([CommandArgType.INT64, CommandArgType.INT32])

        self.argument_types = args
        return super().read(reader, cmd_line_info)


class CommandSubStart(Command):
    def __init__(self):
        super().__init__("SubStart", None)

    def read(
        self, reader: ExtendedBinaryReader, cmd_line_info: Optional[bytes]
    ) -> Command:
        reader.jump_ahead(5)
        count = reader.read_byte()
        reader.jump_behind(6)

        args: List[CommandArgType] = [
            CommandArgType.BYTE,
            CommandArgType.INT32,
            CommandArgType.BYTE,
            CommandArgType.UINT64,
            CommandArgType.BYTE,
        ]

        for _ in range(count):
            args.extend([CommandArgType.BYTE, CommandArgType.NODE])

        args.append(CommandArgType.COMMAND_REF)
        self.argument_types = args
        return super().read(reader, cmd_line_info)


def _make_command(name: str, *types: CommandArgType) -> Command:
    return Command(name, list(types) if types else None)


DALRDCommands = [
    _make_command("Nop"),
    _make_command("Exit"),
    _make_command("Cont", CommandArgType.INT32),
    _make_command("Printf", CommandArgType.NODE),
    _make_command("VWait", CommandArgType.NODE),
    _make_command("Goto", CommandArgType.COMMAND_REF),
    CommandSubStart(),
    _make_command("SubEnd"),
    _make_command("SubEndWait", CommandArgType.BYTE),
    CommandFuncCall(),
    CommandReturn(),
    _make_command("FileJump", CommandArgType.NODE),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("FlgSw", CommandArgType.INT64, CommandArgType.BOOL),
    _make_command("FlgSet", CommandArgType.INT64, CommandArgType.NODE),
    _make_command("ValSet", CommandArgType.INT64, CommandArgType.NODE, CommandArgType.BYTE),
    _make_command("StrSet"),
    _make_command("JumpIf", CommandArgType.UINT32, CommandArgType.NODE),
    CommandJumpSwitch(),
    _make_command("RandVal"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("AutoStop"),
    _make_command("Movie", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.BYTE),
    _make_command("Bgm+ Play/Stop", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BgmVolume", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("SePlay", CommandArgType.NODE, CommandArgType.BOOL),
    _make_command("SeStop", CommandArgType.NODE),
    _make_command("SeWait", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("SeVolume", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("SeAllStop"),
    _make_command("Dummy"),
    _make_command("VoicePlay"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("NowLoading+ Start/Stop", CommandArgType.BOOL),
    _make_command("Fade", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.BYTE),
    _make_command("PatternFade"),
    _make_command("Quake", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("CrossFade", CommandArgType.NODE),
    _make_command("PatternCrossFade", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("DispTone", CommandArgType.NODE),
    _make_command("FadeWait", CommandArgType.NODE),
    _make_command("ExiWait", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("MesQuake", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("SetRootName", CommandArgType.NODE),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Dummy"),
    _make_command("Wait2", CommandArgType.NODE),
    _make_command("Mes", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.STRING, CommandArgType.INT16),
    _make_command("MesWait"),
    _make_command("Name / NameOff", CommandArgType.NODE),
    _make_command("Choice", CommandArgType.UINT32, CommandArgType.STRING, CommandArgType.INT16),
    _make_command("ChoiceStart", CommandArgType.BOOL),
    _make_command("FontSize", CommandArgType.NODE),
    _make_command("MapPlace", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.INT32),
    _make_command("MapChara", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("MapBg", CommandArgType.NODE),
    _make_command("MapCoord", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("MapStart"),
    _make_command("MapInit"),
    _make_command("MesWinClose"),
    _make_command("BgOpen", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BgClose", CommandArgType.NODE),
    _make_command("MaAnime", CommandArgType.NODE),
    _make_command("BgMove", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.BYTE, CommandArgType.BYTE),
    _make_command("BgScale", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.BYTE, CommandArgType.BYTE),
    _make_command("BustOpen", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustClose", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustMove", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustMoveAdd", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustScale", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.BYTE, CommandArgType.BYTE),
    _make_command("BustPriority", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("MesVoice+ 2/Idx", CommandArgType.BYTE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("VoiceCharaDraw", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("DateSet", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("TellOpen", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("TellClose", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("Trophy", CommandArgType.NODE),
    _make_command("Vibraiton"),
    _make_command("BustQuake", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustFade", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustCrossMove"),
    _make_command("BustTone", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("BustAnime", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("CameraMoveXY"),
    _make_command("CameraMoveZ"),
    _make_command("CameraMoveXYZ"),
    _make_command("ScaleMode"),
    _make_command("GetBgNo"),
    _make_command("GetFadeState"),
    _make_command("Ambiguous+ On/Off", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.BYTE),
    _make_command("AmbiguousPowerFade", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("Blur+ On/Off", CommandArgType.NODE, CommandArgType.BYTE),
    _make_command("BlurPowerFade", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("Monologue+ On/Off", CommandArgType.NODE),
    _make_command("Mirage+ On/Off", CommandArgType.NODE, CommandArgType.BOOL),
    _make_command("MiragePowerFade"),
    _make_command("MessageVoiceWait", CommandArgType.NODE),
    _make_command("RasterScroll+ On/Off"),
    _make_command("RasterScrollPowerFade"),
    _make_command("MesDel"),
    _make_command("MemoryOn", CommandArgType.NODE),
    _make_command("SaveDateSet"),
    _make_command("ExiPlay", CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE, CommandArgType.NODE),
    _make_command("ExiStop", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("GalleryFlg", CommandArgType.NODE),
    _make_command("DateChange"),
    _make_command("BustSpeed"),
    _make_command("DateRestNumber", CommandArgType.NODE),
    _make_command("MapTutorial"),
    _make_command("Ending"),
    _make_command("Set/Del +FixAuto"),
    _make_command("ExiLoopStop"),
    _make_command("ExiEndWait", CommandArgType.NODE, CommandArgType.NODE),
    _make_command("Set/Del +EventKeyNg", CommandArgType.BOOL),
    _make_command("BustExpr"),
    _make_command("BustLoadStart"),
    _make_command("BustLoadWait"),
]
