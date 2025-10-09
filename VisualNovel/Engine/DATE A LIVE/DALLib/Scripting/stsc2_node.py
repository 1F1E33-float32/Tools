from enum import IntEnum
from typing import Optional

from DALLib.IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter


class ParamFormatType(IntEnum):
    Auto = 0
    Local = 1


class ParamDataType(IntEnum):
    Int = 0
    Float = 1
    Bool = 2
    String = 3
    StringBuffer = 0x1E
    Void = 0x1F


class ParamStructType(IntEnum):
    Number = 0
    Param = 1
    StringAddress = 2
    StringBuffer = 0x07


class STSC2Node:
    def __init__(self, value: Optional[object] = None) -> None:
        self.Value = value
        self.paramFormatType = ParamFormatType.Auto
        self.paramDataType = ParamDataType.Int
        self.paramStructType = ParamStructType.Number

        self._node_type = 0
        self._operator = 0

        self.LeftNode: Optional["STSC2Node"] = None
        self.RightNode: Optional["STSC2Node"] = None

        self._node_count: int = 0
        self._left_node: int = 0
        self._right_node: int = 0

        if isinstance(value, int):
            self._node_type = 0x01
            self._node_count = 0x01

    def read(self, reader: ExtendedBinaryReader, base_address: int = 0, node_num: int = 0) -> "STSC2Node":
        prev_position = 0
        if node_num == 0:
            address = reader.read_uint32()
            if address == 0:
                return self
            prev_position = reader.get_position()
            reader.jump_to(address)
            self._node_count = reader.read_int16()

        bits = reader.read_byte()
        self._node_type = (bits >> 7) & 0x01
        self._operator = bits & 0x7F
        value_position = reader.get_position()
        reader.jump_ahead(0x06)

        self.paramFormatType = ParamFormatType(reader.read_byte())
        bits = reader.read_byte()
        self.paramDataType = ParamDataType(bits & 0x1F)
        self.paramStructType = ParamStructType((bits & 0xE0) >> 5)

        prev_node_offset = reader.read_int16()
        next_node_offset = reader.read_int16()
        self._left_node = prev_node_offset
        self._right_node = next_node_offset

        if node_num == 0:
            base_address = reader.get_position()

        if prev_node_offset not in (0, 1):
            reader.jump_to(base_address + (prev_node_offset - 2) * 13)
            self.LeftNode = STSC2Node().read(reader, base_address, prev_node_offset)

        if next_node_offset not in (0, 1):
            reader.jump_to(base_address + (next_node_offset - 2) * 13)
            self.RightNode = STSC2Node().read(reader, base_address, next_node_offset)

        reader.jump_to(value_position)
        if self.paramStructType in (ParamStructType.Number, ParamStructType.Param):
            self.Value = reader.read_int32()
        elif self.paramStructType == ParamStructType.StringAddress:
            self.Value = reader.read_string_elsewhere()

        if prev_position:
            reader.jump_to(prev_position)
        return self

    def write(
        self,
        writer: ExtendedBinaryWriter,
        offset: int,
        base_address: int = 0,
        node_num: int = 0,
    ) -> None:
        if node_num == 0:
            writer.write_int16(self._node_count)
            base_address = writer.base_stream.tell()

        writer.write_byte((self._node_type << 7) | (self._operator & 0x7F))

        if self.paramStructType in (ParamStructType.Number, ParamStructType.Param):
            writer.write_int32(int(self.Value) if self.Value is not None else 0)
        elif self.paramStructType == ParamStructType.StringAddress:
            writer.write_uint32(offset)
        else:
            writer.write_int32(0)

        writer.write_nulls(0x02)
        writer.write_byte(self.paramFormatType)
        combined = (self.paramStructType << 5) | (self.paramDataType & 0x1F)
        writer.write_byte(combined)

        writer.write_int16(self._left_node)
        writer.write_int16(self._right_node)

        if self.LeftNode is not None:
            left_pos = 13 * (self._left_node - 1) + base_address
            current = writer.base_stream.tell()
            writer.jump_to(left_pos)
            self.LeftNode.write(writer, offset, base_address, self._left_node)
            writer.jump_to(current)

        if self.RightNode is not None:
            right_pos = 13 * (self._right_node - 1) + base_address
            current = writer.base_stream.tell()
            writer.jump_to(right_pos)
            self.RightNode.write(writer, offset, base_address, self._right_node)
            writer.jump_to(current)

    def __str__(self) -> str:
        return str(self.Value) if self.Value is not None else super().__str__()
