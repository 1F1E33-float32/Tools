import struct
from typing import BinaryIO

from age_shared import Argument, Header, Instruction, cp932_to_utf8, utf16le_to_utf8
from instructions import instruction_for_opcode
from ir import IR
from overflow import u8, u16, u32


def parse_instruction(fd: BinaryIO, header: Header, definition, offset: int, data_array_end: list[int]) -> Instruction:
    arguments = []

    for i in range(definition.arg_count):
        arg_type, raw_data = struct.unpack("<II", fd.read(8))
        arg = Argument(arg_type=arg_type, raw_data=raw_data)

        if arg_type == 2:
            # String argument - read from data section
            string_offset = header.length + u32(raw_data << 2)
            data_array_end[0] = min(data_array_end[0], string_offset)

            cur_pos = fd.tell()
            fd.seek(string_offset)

            if header.is_ver5:
                # UTF-16LE string, XORed with 0xFFFF
                decoded = b""
                while True:
                    char_bytes = fd.read(2)
                    if len(char_bytes) < 2:
                        break
                    char_val = u16(struct.unpack("<H", char_bytes)[0])
                    if char_val == 0xFFFF:
                        break
                    char_val = u16(char_val ^ 0xFFFF)
                    decoded += struct.pack("<H", char_val)
                arg.decoded_string = utf16le_to_utf8(decoded)
            else:
                # CP932 string, XORed with 0xFF
                decoded = b""
                while True:
                    char_byte = fd.read(1)
                    if not char_byte:
                        break
                    char_val = u8(char_byte[0])
                    if char_val == 0xFF:
                        break
                    decoded += bytes([u8(char_val ^ 0xFF)])
                arg.decoded_string = cp932_to_utf8(decoded)

            fd.seek(cur_pos)
        elif definition.op_code == 0x64 and i == 1:
            # Array argument
            array_offset = header.length + u32(raw_data << 2)
            data_array_end[0] = min(data_array_end[0], array_offset)

            cur_pos = fd.tell()
            fd.seek(array_offset)

            length = struct.unpack("<I", fd.read(4))[0]
            data = []
            for _ in range(length):
                data.append(struct.unpack("<I", fd.read(4))[0])
            arg.data_array = data

            fd.seek(cur_pos)

        arguments.append(arg)

    return Instruction(definition, offset, arguments)


def disassemble(fd: BinaryIO) -> IR:
    header = Header(fd=fd)
    hdr = header.header

    # Calculate initial data array end
    min_table_offset = min(hdr.table_1_offset, hdr.table_2_offset, hdr.table_3_offset)
    data_array_end = [header.length + u32(min_table_offset << 2)]

    # Parse instructions
    instructions = []
    while fd.tell() < data_array_end[0]:
        offset = fd.tell()
        op_code = struct.unpack("<I", fd.read(4))[0]

        if op_code == 0:
            raise ValueError(f"Bad opcode 0x{op_code:X} at offset 0x{offset:X}")

        definition = instruction_for_opcode(op_code, offset)
        instr_offset = u32((offset - header.length) >> 2)
        instruction = parse_instruction(fd, header, definition, instr_offset, data_array_end)
        instructions.append(instruction)

    return IR(header=header, instructions=instructions)
