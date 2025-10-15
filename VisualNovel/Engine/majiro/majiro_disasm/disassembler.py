import json
import struct
import sys
from io import BytesIO
from typing import BinaryIO, List, TextIO

from .crc import Crc
from .flags import MjoFlags, MjoScope, MjoType
from .instruction import Instruction
from .known_names import KnownNames
from .opcode import OpcodeRegistry
from .script import FunctionIndexEntry, MjoScript, MjoScriptRepresentation


class Disassembler:
    @staticmethod
    def disassemble_from_file(path: str) -> MjoScript:
        with open(path, "rb") as f:
            return Disassembler.disassemble_script(f)

    @staticmethod
    def disassemble_script(reader: BinaryIO) -> MjoScript:
        # Read signature
        signature = reader.read(16).decode("ascii", errors="ignore")
        is_encrypted = signature == "MajiroObjX1.000\0"

        if not is_encrypted and signature != "MajiroObjV1.000\0":
            raise ValueError(f"Invalid signature: {signature!r}")

        # Read header
        entry_point_offset = struct.unpack("<I", reader.read(4))[0]
        read_mark_size = struct.unpack("<I", reader.read(4))[0]
        function_count = struct.unpack("<i", reader.read(4))[0]

        # Read function index
        function_index = []
        for _ in range(function_count):
            name_hash = struct.unpack("<I", reader.read(4))[0]
            offset = struct.unpack("<I", reader.read(4))[0]
            function_index.append(FunctionIndexEntry(name_hash, offset))

        # Read bytecode
        bytecode_size = struct.unpack("<i", reader.read(4))[0]
        bytecode = bytearray(reader.read(bytecode_size))

        # Decrypt if necessary
        if is_encrypted:
            Crc.crypt_32(bytecode)

        # Create script object
        script = MjoScript(
            representation=MjoScriptRepresentation.INSTRUCTION_LIST,
            instructions=[],
            entry_point_offset=entry_point_offset,
            function_index=function_index,
            enable_read_mark=(read_mark_size != 0),
        )

        Disassembler.disassemble_bytecode(BytesIO(bytecode), script.instructions)

        return script

    @staticmethod
    def disassemble_bytecode(stream: BinaryIO, instructions: List[Instruction]) -> None:
        while True:
            offset = stream.tell()
            if offset >= len(stream.getvalue()):
                break

            instruction = Disassembler.read_instruction(stream, offset)
            instructions.append(instruction)

    @staticmethod
    def read_instruction(reader: BinaryIO, offset: int) -> Instruction:
        # Read opcode
        opcode_value = struct.unpack("<H", reader.read(2))[0]
        opcode = OpcodeRegistry.get_by_value(opcode_value)

        if opcode is None:
            raise ValueError(f"Invalid opcode at offset 0x{offset:08X}: 0x{opcode_value:04X}")

        instruction = Instruction(opcode=opcode, offset=offset)
        encoding = opcode.encoding

        # Parse operands based on encoding
        for operand_char in encoding:
            if operand_char == "t":
                # Type list
                count = struct.unpack("<H", reader.read(2))[0]
                instruction.type_list = [MjoType(b) for b in reader.read(count)]

            elif operand_char == "s":
                # String data
                size = struct.unpack("<H", reader.read(2))[0]
                string_bytes = reader.read(size - 1)
                null_terminator = reader.read(1)
                assert null_terminator == b"\x00", "Expected null terminator"
                instruction.string = string_bytes.decode("shift-jis", errors="replace")

            elif operand_char == "f":
                # Flags
                instruction.flags = struct.unpack("<H", reader.read(2))[0]

            elif operand_char == "h":
                # Name hash
                instruction.hash = struct.unpack("<I", reader.read(4))[0]

            elif operand_char == "o":
                # Variable offset
                instruction.var_offset = struct.unpack("<h", reader.read(2))[0]

            elif operand_char == "0":
                # 4-byte address placeholder
                placeholder = struct.unpack("<I", reader.read(4))[0]
                assert placeholder == 0, "Expected address placeholder to be 0"

            elif operand_char == "i":
                # Integer constant
                instruction.int_value = struct.unpack("<i", reader.read(4))[0]

            elif operand_char == "r":
                # Float constant
                instruction.float_value = struct.unpack("<f", reader.read(4))[0]

            elif operand_char == "a":
                # Argument count
                instruction.argument_count = struct.unpack("<H", reader.read(2))[0]

            elif operand_char == "j":
                # Jump offset
                instruction.jump_offset = struct.unpack("<i", reader.read(4))[0]

            elif operand_char == "l":
                # Line number
                instruction.line_number = struct.unpack("<H", reader.read(2))[0]

            elif operand_char == "c":
                # Switch case table
                count = struct.unpack("<H", reader.read(2))[0]
                instruction.switch_offsets = [struct.unpack("<i", reader.read(4))[0] for _ in range(count)]

            else:
                raise ValueError(f"Unrecognized encoding specifier: {operand_char}")

        # Calculate instruction size
        instruction.size = reader.tell() - offset

        return instruction

    @staticmethod
    def print_script(script: MjoScript, writer: TextIO = None) -> None:
        if writer is None:
            writer = sys.stdout

        # Print readmark setting
        writer.write(f"readmark {'enable' if script.enable_read_mark else 'disable'}\n\n")

        # Print function index
        if script.function_index:
            for entry in script.function_index:
                is_entry = entry.offset == script.entry_point_offset
                writer.write(f"index ${entry.name_hash:08x} 0x{entry.offset:04x}")
                if is_entry:
                    writer.write(" entrypoint")
                writer.write("\n")
            writer.write("\n")

        # Print instructions
        if script.instructions:
            for instruction in script.instructions:
                Disassembler.print_instruction(instruction, writer)

    @staticmethod
    def print_instruction(instruction: Instruction, writer: TextIO = None) -> None:
        if writer is None:
            writer = sys.stdout

        # Print offset
        if instruction.offset is not None:
            writer.write(f"{instruction.offset:04x}: ")

        # Print mnemonic
        writer.write(f"{instruction.opcode.mnemonic:<13} ")

        # Print operands
        encoding = instruction.opcode.encoding
        first_operand = True

        for operand_char in encoding:
            if operand_char == "0":
                continue

            if not first_operand:
                writer.write(" ")
            first_operand = False

            # Skip printing var_offset for non-local variables with offset -1
            if operand_char == "o" and MjoFlags.scope(instruction.flags) != MjoScope.LOCAL and instruction.var_offset == -1:
                continue

            if operand_char == "t":
                # Type list
                writer.write("[")
                writer.write(", ".join(t.name.lower() for t in instruction.type_list))
                writer.write("]")

            elif operand_char == "s":
                # String
                if instruction.string is not None:
                    escaped = instruction.string.replace("\\", "\\\\").replace('"', '\\"')
                    writer.write(f'"{escaped}"')
                elif instruction.external_key is not None:
                    writer.write(f"%{{{instruction.external_key}}}")

            elif operand_char == "f":
                # Flags
                scope = MjoFlags.scope(instruction.flags)
                type_val = MjoFlags.type(instruction.flags)
                writer.write(f"{scope.name.lower()} {type_val.name.lower()}")

                invert = MjoFlags.invert_mode(instruction.flags)
                if invert.value != 0:
                    writer.write(f" invert_{invert.name.lower()}")

                modifier = MjoFlags.modifier(instruction.flags)
                if modifier.value != 0:
                    writer.write(f" {modifier.name.lower()}")

                dimension = MjoFlags.dimension(instruction.flags)
                if dimension > 0:
                    writer.write(f" dim{dimension}")

            elif operand_char == "h":
                # Hash - with known name lookup
                hash_val = instruction.hash

                # Check if this is a syscall or regular call
                if instruction.is_syscall:
                    # Try to find syscall name
                    name = KnownNames.get_syscall_name(hash_val)
                    if name:
                        writer.write(f"$${name}@MAJIRO_INTER")
                    else:
                        writer.write(f"${hash_val:08x}")
                elif instruction.is_call:
                    # Try to find function name
                    name = KnownNames.get_function_name(hash_val)
                    if name:
                        writer.write(f"${name}")
                    else:
                        writer.write(f"${hash_val:08x}")
                elif instruction.is_load or instruction.is_store:
                    # Try to find variable name
                    name = KnownNames.get_variable_name(hash_val)
                    if name:
                        writer.write(f"${name}")
                    else:
                        writer.write(f"${hash_val:08x}")
                else:
                    writer.write(f"${hash_val:08x}")

            elif operand_char == "o":
                # Variable offset
                writer.write(str(instruction.var_offset))

            elif operand_char == "i":
                # Integer
                writer.write(str(instruction.int_value))

            elif operand_char == "r":
                # Float
                writer.write(f"{instruction.float_value:.6f}")

            elif operand_char == "a":
                # Argument count
                writer.write(f"({instruction.argument_count})")

            elif operand_char == "j":
                # Jump offset
                offset = instruction.jump_offset
                if offset < 0:
                    writer.write(f"@~-{-offset:04x}")
                elif offset > 0:
                    writer.write(f"@~+{offset:04x}")
                else:
                    writer.write("@~0")

            elif operand_char == "l":
                # Line number
                writer.write(f"#{instruction.line_number}")

            elif operand_char == "c":
                # Switch offsets
                if instruction.switch_offsets:
                    for i, offset in enumerate(instruction.switch_offsets):
                        if i > 0:
                            writer.write(", ")
                        if offset < 0:
                            writer.write(f"@~-{-offset:04x}")
                        elif offset > 0:
                            writer.write(f"@~+{offset:04x}")
                        else:
                            writer.write("@~0")

        # Add comment with known names
        if instruction.is_call or instruction.is_syscall:
            hash_val = instruction.hash
            if instruction.is_syscall:
                name = KnownNames.get_syscall_name(hash_val)
                if name:
                    writer.write(f" ; ${name}@MAJIRO_INTER")
            else:
                name = KnownNames.get_function_name(hash_val)
                if name:
                    writer.write(f" ; {name}")
        elif instruction.is_load or instruction.is_store:
            hash_val = instruction.hash
            name = KnownNames.get_variable_name(hash_val)
            if name:
                writer.write(f" ; {name}")

        writer.write("\n")


    @staticmethod
    def render_to_json(script: MjoScript, writer: TextIO = None, indent: int = 2) -> None:
        if writer is None:
            writer = sys.stdout
        
        json.dump(script.to_dict(), writer, ensure_ascii=False, indent=indent)
        writer.write("\n")


def disassemble_file(input_path: str, output_path: str = None, print_console: bool = False) -> None:
    script = Disassembler.disassemble_from_file(input_path)

    if print_console:
        Disassembler.print_script(script)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            Disassembler.print_script(script, f)
