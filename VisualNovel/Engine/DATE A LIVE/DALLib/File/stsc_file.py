from typing import Dict, List, Optional

from DALLib.Exceptions import STSCDisassembleException
from DALLib.IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter
from DALLib.Scripting import DALRRInstructions, Instruction

from .file_base import FileBase


class STSCFile(FileBase):
    def __init__(self):
        super().__init__()
        self.script_name: str = ""
        self.script_id: int = 0
        self.instructions: List[Instruction] = []
        self.manual_count: int = 0
        self.use_small_header: bool = False
        self.version: int = 0x07

    def load_from_reader(self, reader: ExtendedBinaryReader, keep_open: bool = False):
        signature = reader.read_signature()
        if signature == "STSC":
            header_size = reader.read_uint32()
            self.version = reader.read_uint32()
            if self.version == 4:
                self.script_id = reader.read_uint16()
            elif self.version == 7:
                self.script_name = reader.read_null_terminated_string() or ""
                padding = max(0, 0x20 - (len(self.script_name) + 1))
                reader.jump_ahead(padding)
                reader.jump_ahead(12)
                self.script_id = reader.read_uint32()
            else:
                reader.jump_ahead(max(0, header_size - 8))
        else:
            reader.jump_behind(4)
            self.script_id = reader.read_uint16()

        reader.offset = reader.get_length()
        self.instructions.clear()

        while True:
            opcode_position = reader.get_position()
            opcode = reader.read_byte()

            if opcode >= len(DALRRInstructions):
                raise STSCDisassembleException(self, f"Got opcode 0x{opcode:02X} at 0x{opcode_position:08X}. There are no opcodes beyond 0x93!")

            template = DALRRInstructions[opcode]
            if template is None:
                raise STSCDisassembleException(self, f"Got opcode 0x{opcode:02X} at 0x{opcode_position:08X}. This opcode is unknown!")

            instruction = template.read(reader)
            self.instructions.append(instruction)

            if reader.base_stream.tell() >= reader.offset:
                break

    def save_from_writer(self, writer: ExtendedBinaryWriter):
        string_table: List[str] = []

        writer.write_signature("STSC")
        writer.add_offset("EntryPosition")
        writer.write_uint32(self.version)

        if self.version == 4:
            writer.write_uint16(self.script_id)
        elif self.version == 7:
            name_bytes = self.script_name.encode("utf-8")
            writer.write_bytes(name_bytes)
            writer.write_null()
            remaining = max(0, 0x20 - (len(name_bytes) + 1))
            writer.write_nulls(remaining)
            writer.write_uint32(0x000507E3)
            writer.write_int16(0x09)
            writer.write_int16(0x0D)
            writer.write_int16(0x19)
            writer.write_int16(0x0D)
            writer.write_uint32(self.script_id)
        else:
            writer.write_uint32(self.script_id)

        writer.fill_in_offset("EntryPosition")

        self.manual_count = 0
        for instruction in self.instructions:
            opcode = self._find_opcode(instruction.name)
            if opcode is None:
                raise ValueError(f"Unable to find opcode for instruction '{instruction.name}'.")
            writer.write_byte(opcode)
            self.manual_count = instruction.write(writer, self.manual_count, string_table)

        written_strings: Dict[str, int] = {}
        for index, value in enumerate(string_table):
            if not writer.has_offset(f"Strings_{index}"):
                continue
            if value in written_strings:
                writer.fill_in_offset(f"Strings_{index}", written_strings[value])
                continue
            writer.fill_in_offset(f"Strings_{index}")
            written_strings[value] = writer.base_stream.tell()
            writer.write_null_terminated_string(value)

        writer.fix_padding(0x10)

    def find_address(self, index: int) -> int:
        address = 0
        for i in range(index):
            address += self.instructions[i].get_instruction_size()
        return address

    def find_index(self, address: int) -> int:
        temp_address = 0x0E if self.version == 4 else 0x3C
        for idx, instruction in enumerate(self.instructions):
            if temp_address >= address:
                return idx
            temp_address += instruction.get_instruction_size()
        return 0

    def _find_opcode(self, name: str) -> Optional[int]:
        for index, instruction in enumerate(DALRRInstructions):
            if instruction and instruction.name == name:
                return index
        return None

    def __str__(self) -> str:
        return self.script_name
