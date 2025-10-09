from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, List, Optional, Sequence

from DALLib.IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter, StreamBlock


class ArgumentType(Enum):
    AT_Bool = 0
    AT_Byte = 1
    AT_Int16 = 2
    AT_Int32 = 3
    AT_Float = 4
    AT_String = 5
    AT_StringPtr = 6
    AT_CodePointer = 7
    AT_DataReference = 8
    AT_PointerArray = 9
    AT_DataBlock = 10


@dataclass
class Instruction:
    name: str
    arg_types: Optional[Sequence[ArgumentType]]
    arguments: List[Any] = field(default_factory=list)

    def get_argument(self, index: int) -> Any:
        return self.arguments[index]

    def read(self, reader: ExtendedBinaryReader) -> "Instruction":
        instruction = Instruction(self.name, self.arg_types)
        if not self.arg_types:
            return instruction

        for arg_type in self.arg_types:
            if arg_type == ArgumentType.AT_PointerArray:
                pointer_count = reader.read_byte()
                pointers = [reader.read_int32() for _ in range(pointer_count)]
                instruction.arguments.append(pointers)
            else:
                instruction.arguments.append(read_by_type(reader, arg_type))

        return instruction

    def write(
        self,
        writer: ExtendedBinaryWriter,
        manual_count: int,
        strings: Optional[List[str]] = None,
    ) -> int:
        if not self.arg_types:
            return manual_count

        for index, arg_type in enumerate(self.arg_types):
            if arg_type == ArgumentType.AT_PointerArray:
                pointers = self.get_argument(index)
                writer.write_byte(len(pointers))
                for pointer in pointers:
                    writer.write_int32(pointer)
            else:
                manual_count = write_by_type(writer, arg_type, self.arguments[index], manual_count, strings)

        return manual_count

    def get_instruction_size(self) -> int:
        size = 1
        if not self.arg_types:
            return size

        for index, arg in enumerate(self.arg_types):
            if arg in (ArgumentType.AT_Bool, ArgumentType.AT_Byte):
                size += 1
            elif arg == ArgumentType.AT_Int16:
                size += 2
            elif arg in (ArgumentType.AT_Int32, ArgumentType.AT_CodePointer, ArgumentType.AT_DataReference, ArgumentType.AT_Float, ArgumentType.AT_String, ArgumentType.AT_DataBlock):
                size += 4
            elif arg == ArgumentType.AT_PointerArray:
                pointers = self.get_argument(index)
                size += len(pointers) * 4 + 1

        return size


class ComparisonOperators(IntEnum):
    Equals = 0
    NotEquals = 1
    GreaterThenOrEqual = 2
    GreaterThan = 3
    LessThenOrEqual = 4
    LessThen = 5
    NotZero = 6
    Zero = 7


@dataclass
class InstructionIf(Instruction):
    comparisons: List["Comparison"] = field(default_factory=list)

    @dataclass
    class Comparison:
        left: int
        operator: ComparisonOperators
        right: int

    def __init__(self) -> None:
        super().__init__("if", [ArgumentType.AT_CodePointer])
        self.comparisons = []

    def read(self, reader: ExtendedBinaryReader) -> "InstructionIf":
        instruction = InstructionIf()
        amount = reader.read_int16()
        instruction.arguments.append(reader.read_int32())
        for _ in range(amount):
            left = reader.read_uint32()
            right = reader.read_uint32()
            operator = ComparisonOperators(reader.read_byte())
            instruction.comparisons.append(InstructionIf.Comparison(left, operator, right))
        return instruction

    def write(
        self,
        writer: ExtendedBinaryWriter,
        manual_count: int,
        strings: Optional[List[str]] = None,
    ) -> int:
        writer.write_int16(len(self.comparisons))
        writer.write_int32(self.get_argument(0))
        for comparison in self.comparisons:
            writer.write_uint32(comparison.left)
            writer.write_uint32(comparison.right)
            writer.write_byte(comparison.operator.value)
        return manual_count

    def get_instruction_size(self) -> int:
        return 1 + 2 + 4 + len(self.comparisons) * 9


@dataclass
class InstructionSwitch(Instruction):
    def read(self, reader: ExtendedBinaryReader) -> "InstructionSwitch":
        instruction = InstructionSwitch(self.name, self.arg_types)
        unknown = reader.read_uint32()
        amount = reader.read_uint16()
        end_flag = amount >> 15 == 1
        if end_flag:
            amount &= 0x7FF

        arg_types = [ArgumentType.AT_DataReference, ArgumentType.AT_Int16, ArgumentType.AT_Bool]
        arguments = [unknown, amount, end_flag]
        for _ in range(amount):
            arguments.append(reader.read_int32())
            arguments.append(reader.read_int32())
            arg_types.extend([ArgumentType.AT_Int32, ArgumentType.AT_CodePointer])

        instruction.arg_types = arg_types
        instruction.arguments = arguments
        return instruction

    def write(
        self,
        writer: ExtendedBinaryWriter,
        manual_count: int,
        strings: Optional[List[str]] = None,
    ) -> int:
        writer.write_uint32(self.get_argument(0))
        value = self.get_argument(1)
        flag = self.get_argument(2)
        writer.write_uint16(value | (int(flag) << 15))

        for index in range(self.get_argument(1)):
            case_value = self.get_argument(index * 2 + 3)
            location = self.get_argument(index * 2 + 4)
            writer.write_int32(case_value)
            writer.write_int32(location)

        return manual_count

    def get_instruction_size(self) -> int:
        # Mirror the "cheap way" from the C# version by subtracting a byte.
        base_size = super().get_instruction_size()
        return base_size - 1 if base_size > 0 else 0


def read_by_type(reader: ExtendedBinaryReader, arg_type: ArgumentType) -> Any:
    if arg_type == ArgumentType.AT_Bool:
        return reader.read_bool()
    if arg_type == ArgumentType.AT_Byte:
        return reader.read_byte()
    if arg_type == ArgumentType.AT_Int16:
        return reader.read_int16()
    if arg_type == ArgumentType.AT_Int32:
        return reader.read_int32()
    if arg_type == ArgumentType.AT_Float:
        return reader.read_single()
    if arg_type == ArgumentType.AT_String:
        return reader.read_string_elsewhere()
    if arg_type == ArgumentType.AT_StringPtr:
        return reader.read_null_terminated_string_pointer()
    if arg_type == ArgumentType.AT_CodePointer:
        return reader.read_int32()
    if arg_type == ArgumentType.AT_DataReference:
        return reader.read_uint32()
    if arg_type == ArgumentType.AT_DataBlock:
        position = reader.read_uint32()
        length = reader.read_uint32()
        if reader.offset > position:
            reader.offset = position
        return StreamBlock(position, length)
    if arg_type == ArgumentType.AT_PointerArray:
        pointer_count = reader.read_byte()
        return [reader.read_int32() for _ in range(pointer_count)]
    return None


def write_by_type(
    writer: ExtendedBinaryWriter,
    arg_type: ArgumentType,
    value: Any,
    manual_count: int,
    strings: Optional[List[str]],
) -> int:
    if arg_type == ArgumentType.AT_Bool:
        writer.write_bool(bool(value))
    elif arg_type == ArgumentType.AT_Byte:
        writer.write_byte(int(value))
    elif arg_type == ArgumentType.AT_Int16:
        writer.write_int16(int(value))
    elif arg_type == ArgumentType.AT_Int32:
        writer.write_int32(int(value))
    elif arg_type == ArgumentType.AT_Float:
        writer.write_single(float(value))
    elif arg_type == ArgumentType.AT_String:
        if strings is None:
            return manual_count
        if value is None:
            writer.write_int32(0)
        else:
            writer.add_offset(f"Strings_{len(strings)}")
            strings.append(str(value))
    elif arg_type == ArgumentType.AT_StringPtr:
        if strings is None:
            return manual_count
        writer.add_offset(f"StringsPtr_{len(strings)}")
        strings.append(str(value))
    elif arg_type == ArgumentType.AT_CodePointer:
        writer.write_int32(int(value))
    elif arg_type == ArgumentType.AT_DataReference:
        writer.write_int32(int(value))
    elif arg_type == ArgumentType.AT_DataBlock:
        writer.add_offset(f"Manual_Ptr_{manual_count}l")
        writer.add_offset(f"Manual_Ptr_{manual_count}h")
        manual_count += 1
    elif arg_type == ArgumentType.AT_PointerArray:
        pointers = value or []
        writer.write_byte(len(pointers))
        for pointer in pointers:
            writer.write_int32(int(pointer))
    return manual_count


PBBInstructions = [
    Instruction("NOP", None),
    Instruction("Exit", None),
    Instruction("Continue", [ArgumentType.AT_Byte]),
    Instruction("Endv", None),
    None,
    Instruction("VWait", [ArgumentType.AT_Int32]),
    Instruction("Goto", [ArgumentType.AT_CodePointer]),
    Instruction("Return", None),
    None,
    None,
    None,
    Instruction("SubStart", [ArgumentType.AT_Byte, ArgumentType.AT_CodePointer]),
    Instruction("SubEnd", [ArgumentType.AT_Byte]),
    Instruction("RandJmp", [ArgumentType.AT_PointerArray]),
    Instruction("Printf", [ArgumentType.AT_String]),
    Instruction("FileJump", [ArgumentType.AT_String]),
    None,
    Instruction("NgFlg", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    Instruction("FlgSw", [ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    None,
    None,
    Instruction("SetPrm", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    None,
    Instruction("AddPrm", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    None,
    None,
    Instruction("Call", [ArgumentType.AT_CodePointer]),
    Instruction("CallRet", None),
    None,
    InstructionIf(),
    InstructionSwitch("switch", None),
    None,
    Instruction("DataBaseParam", [ArgumentType.AT_Byte, ArgumentType.AT_DataBlock]),
    Instruction("CourseFlag", [ArgumentType.AT_Int16]),
    Instruction("SetNowScenario", [ArgumentType.AT_Int16]),
    None,
    Instruction("CrossFade", [ArgumentType.AT_Int16]),
    Instruction("PatternCrossFade", [ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("DispTone", [ArgumentType.AT_Byte]),
    Instruction("Monologue", [ArgumentType.AT_Bool]),
    Instruction("ExiPlay", [ArgumentType.AT_Int32, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int32, ArgumentType.AT_Byte]),
    Instruction("ExiStop", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("PatternFade", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("Ambiguous", [ArgumentType.AT_Float, ArgumentType.AT_Byte, ArgumentType.AT_Bool]),
    Instruction("AmbiguousFade", [ArgumentType.AT_Float, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("TouchWait", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("CourseFlagGet", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("Chapter", [ArgumentType.AT_Int16]),
    Instruction("Movie", [ArgumentType.AT_String, ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("BgmPlay", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("BgmVolume", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("SePlay", [ArgumentType.AT_Int32, ArgumentType.AT_Bool]),
    Instruction("SeStop", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    None,
    Instruction("SeVolume", [ArgumentType.AT_Int32, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("SeAllStop", [ArgumentType.AT_Int16]),
    None,
    None,
    Instruction("VoiceWait", [ArgumentType.AT_Byte]),
    None,
    Instruction("Dummy3C", None),
    Instruction("Dummy3D", None),
    None,
    Instruction("GetCountry", [ArgumentType.AT_Int32]),
    Instruction("BgOpen", [ArgumentType.AT_Int32, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BgClose", [ArgumentType.AT_Byte]),
    Instruction("BgFrame", [ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("BgMove", [ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("BgScale", [ArgumentType.AT_Float, ArgumentType.AT_Int16, ArgumentType.AT_Byte, ArgumentType.AT_Bool]),
    Instruction("BustOpen", [ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("BustClose", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("BustMove", [ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BustMoveAdd", [ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BustScale", [ArgumentType.AT_Byte, ArgumentType.AT_Float, ArgumentType.AT_Int16, ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("BustPriority", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("BustQuake", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("SetEntryCharFlg", [ArgumentType.AT_Byte]),
    Instruction("BustTone", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("BustFade", [ArgumentType.AT_Byte, ArgumentType.AT_Float, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("Name", [ArgumentType.AT_String]),
    Instruction("Message", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_String, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("MessageWait", [ArgumentType.AT_Bool]),
    Instruction("MessageWinClose", None),
    Instruction("MessageFontSize", [ArgumentType.AT_Byte]),
    Instruction("MessageQuake", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("Trophy", [ArgumentType.AT_Byte]),
    Instruction("MessageDelete", None),
    Instruction("Quake", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("Fade", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("Choice", [ArgumentType.AT_CodePointer, ArgumentType.AT_String, ArgumentType.AT_Int16]),
    Instruction("ChoiceStart", None),
    Instruction("GetBg", [ArgumentType.AT_Int32]),
    Instruction("FontColor", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("WorldType", [ArgumentType.AT_Byte]),
    Instruction("GetWorld", [ArgumentType.AT_Int32]),
    Instruction("Flowchart", [ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("MiniGame", [ArgumentType.AT_Byte, ArgumentType.AT_String]),
    Instruction("CourseOpenGet", [ArgumentType.AT_Int16, ArgumentType.AT_Int32]),
    Instruction("SystemSave", None),
    None,
    None,
    None,
    None,
    Instruction("DataSave", None),
    Instruction("SkipStop", None),
    Instruction("MessageVoice", [ArgumentType.AT_String, ArgumentType.AT_String]),
    None,
    Instruction("SaveNg", [ArgumentType.AT_Bool]),
    Instruction("Dummy6C", None),
    Instruction("Dummy6D", None),
    Instruction("Dummy6E", None),
    None,
    Instruction("ExiLoopStop", [ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("ExiEndWait", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("ClearSet", [ArgumentType.AT_Byte]),
    None,
    Instruction("Dummy74", None),
    Instruction("Dummy75", None),
    Instruction("Dummy76", None),
    Instruction("Dummy77", None),
    None,
    None,
    None,
    None,
    Instruction("Dummy7C", None),
    Instruction("Dummy7D", None),
    Instruction("Dummy7E", None),
    Instruction("Dummy7F", None),
    Instruction("Dummy80", None),
    Instruction("Dummy81", None),
    Instruction("Dummy82", None),
    Instruction("Dummy83", None),
    Instruction("Dummy84", None),
    Instruction("Dummy85", None),
    Instruction("Dummy86", None),
    Instruction("Dummy87", None),
    Instruction("Dummy88", None),
    Instruction("Dummy89", None),
    Instruction("Dummy8A", None),
    Instruction("Dummy8B", None),
    Instruction("Dummy8C", None),
    Instruction("Dummy8D", None),
    Instruction("Dummy8E", None),
    Instruction("Dummy8F", None),
    Instruction("Dummy90", None),
    Instruction("Dummy91", None),
    Instruction("Dummy92", None),
    Instruction("Dummy93", None),
]

DALRRInstructions = [
    Instruction("NOP", None),
    Instruction("Exit", None),
    Instruction("continue", None),
    Instruction("Endv", None),
    None,
    Instruction("Wait", [ArgumentType.AT_Int32]),
    Instruction("Goto", [ArgumentType.AT_CodePointer]),
    Instruction("return", None),
    None,
    None,
    None,
    Instruction("SubStart", [ArgumentType.AT_Byte, ArgumentType.AT_CodePointer]),
    Instruction("SubEnd", [ArgumentType.AT_Byte]),
    Instruction("RandJump", [ArgumentType.AT_PointerArray]),
    Instruction("Printf", [ArgumentType.AT_String]),
    Instruction("FileJump", [ArgumentType.AT_String]),
    None,
    None,
    Instruction("FlagSet", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    None,
    None,
    Instruction("PrmSet", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    Instruction("PrmCopy", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    Instruction("PrmAdd", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    None,
    None,
    Instruction("Call", [ArgumentType.AT_CodePointer]),
    Instruction("CallReturn", None),
    None,
    InstructionIf(),
    InstructionSwitch("switch", None),
    None,
    Instruction("DataBaseParam", [ArgumentType.AT_Byte, ArgumentType.AT_DataBlock]),
    Instruction("NewGameOpen", None),
    Instruction("EventStartMes", [ArgumentType.AT_String]),
    Instruction("Dummy23", None),
    Instruction("Dummy24", None),
    Instruction("Dummy25", None),
    Instruction("Dummy26", None),
    Instruction("Dummy27", None),
    Instruction("Dummy28", None),
    Instruction("Dummy29", None),
    Instruction("Dummy2A", None),
    Instruction("Dummy2B", None),
    Instruction("Dummy2C", None),
    Instruction("Dummy2D", None),
    Instruction("Dummy2E", None),
    None,
    Instruction("PlayMovie", [ArgumentType.AT_String, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BgmWait", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("BgmVolume", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("SePlay", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Bool]),
    Instruction("SeStop", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    None,
    Instruction("SeVolume", [ArgumentType.AT_Int16, ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("SeAllStop", None),
    Instruction("BgmDummy", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("Dummy39", None),
    Instruction("Dummy3A", None),
    Instruction("Dummy3B", None),
    Instruction("Dummy3C", None),
    Instruction("Dummy3D", None),
    Instruction("Dummy3E", None),
    Instruction("Dummy3F", None),
    Instruction("SetNowLoading", [ArgumentType.AT_Bool]),
    Instruction("Fade", [ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("PatternFade", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("Quake", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("CrossFade", [ArgumentType.AT_Int16]),
    Instruction("PatternCrossFade", [ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("DispTone", [ArgumentType.AT_Byte]),
    Instruction("Dummy47", None),
    Instruction("Dummy48", None),
    Instruction("Dummy49", None),
    Instruction("Dummy4A", None),
    Instruction("Dummy4B", None),
    Instruction("Dummy4C", None),
    Instruction("Dummy4D", None),
    Instruction("Dummy4E", None),
    Instruction("Wait2", [ArgumentType.AT_Int32]),
    Instruction("Mes", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_String, ArgumentType.AT_Int16]),
    Instruction("MesWait", None),
    Instruction("MesTitle", [ArgumentType.AT_Byte]),
    Instruction("SetChoice", [ArgumentType.AT_CodePointer, ArgumentType.AT_String, ArgumentType.AT_Int16]),
    Instruction("ShowChoices", [ArgumentType.AT_Bool]),
    Instruction("SetFontSize", [ArgumentType.AT_Byte]),
    Instruction("MapPlace", [ArgumentType.AT_Int16, ArgumentType.AT_String, ArgumentType.AT_CodePointer]),
    Instruction("MapChara", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("MapBg", [ArgumentType.AT_Byte]),
    Instruction("MapCoord", [ArgumentType.AT_Int16, ArgumentType.AT_Byte, ArgumentType.AT_Bool, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("MapStart", None),
    Instruction("MapInit", None),
    Instruction("MesWinClose", None),
    Instruction("BgOpen", [ArgumentType.AT_Int32, ArgumentType.AT_Int32]),
    Instruction("BgClose", [ArgumentType.AT_Byte]),
    Instruction("MaAnime", [ArgumentType.AT_Byte]),
    Instruction("BgMove", [ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("BgScale", [ArgumentType.AT_Float, ArgumentType.AT_Int16, ArgumentType.AT_Byte, ArgumentType.AT_Bool]),
    Instruction("BustOpen", [ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BustClose", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("BustMove", [ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BustMoveAdd", [ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("BustScale", [ArgumentType.AT_Byte, ArgumentType.AT_Float, ArgumentType.AT_Int16, ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("BustPriority", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("PlayVoice", [ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_String]),
    Instruction("VoiceCharaDraw", [ArgumentType.AT_Int16]),
    Instruction("DateSet", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("TellOpen", [ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("TellClose", [ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("Trophy", [ArgumentType.AT_Byte]),
    Instruction("SetVibration", [ArgumentType.AT_Byte, ArgumentType.AT_Float]),
    Instruction("BustQuake", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Int16]),
    Instruction("BustFade", [ArgumentType.AT_Byte, ArgumentType.AT_Float, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("BustCrossMove", None),
    Instruction("BustTone", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("BustAnime", [ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    None,
    None,
    Instruction("CameraMoveXYZ", [ArgumentType.AT_Int16, ArgumentType.AT_Int16, ArgumentType.AT_Float, ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("ScaleMode", [ArgumentType.AT_Byte]),
    Instruction("GetBgNo", [ArgumentType.AT_Int32]),
    Instruction("GetFadeState", [ArgumentType.AT_Int32]),
    Instruction("SetAmbiguous", [ArgumentType.AT_Float, ArgumentType.AT_Byte, ArgumentType.AT_Bool]),
    Instruction("AmbiguousPowerFade", [ArgumentType.AT_Float, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("SetBlur", [ArgumentType.AT_Int32, ArgumentType.AT_Bool]),
    Instruction("BlurPowerFade", [ArgumentType.AT_Float, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("EnableMonologue", [ArgumentType.AT_Byte]),
    Instruction("SetMirage", [ArgumentType.AT_Float, ArgumentType.AT_Bool]),
    Instruction("MiragePowerFade", [ArgumentType.AT_Int32, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("MessageVoiceWait", [ArgumentType.AT_Byte]),
    Instruction("SetRasterScroll", [ArgumentType.AT_Byte, ArgumentType.AT_Float, ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("RasterScrollPowerFade", [ArgumentType.AT_Int32, ArgumentType.AT_Float, ArgumentType.AT_Int16]),
    Instruction("MesDel", None),
    Instruction("MemoryOn", [ArgumentType.AT_Int16]),
    Instruction("SaveDateSet", [ArgumentType.AT_Byte, ArgumentType.AT_String]),
    Instruction("ExiPlay", [ArgumentType.AT_Int16, ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Int32, ArgumentType.AT_Byte]),
    Instruction("ExiStop", [ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("GalleryFlg", [ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("DateChange", [ArgumentType.AT_Int32, ArgumentType.AT_Int16]),
    Instruction("BustSpeed", [ArgumentType.AT_Byte, ArgumentType.AT_Int32]),
    Instruction("DateRestNumber", [ArgumentType.AT_Byte]),
    Instruction("MapTutorial", [ArgumentType.AT_Int16, ArgumentType.AT_Int16]),
    Instruction("Ending", [ArgumentType.AT_Byte]),
    Instruction("Set/Del+FixAuto", [ArgumentType.AT_Byte, ArgumentType.AT_Byte, ArgumentType.AT_Byte]),
    Instruction("ExiLoopStop", [ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("ExiEndWait", [ArgumentType.AT_Int16, ArgumentType.AT_Byte]),
    Instruction("Set/Del+EventKeyNg", [ArgumentType.AT_Byte]),
]

# Provide compatibility aliases similar to the original API surface.
InstructionIf.ComparisonOperators = ComparisonOperators
