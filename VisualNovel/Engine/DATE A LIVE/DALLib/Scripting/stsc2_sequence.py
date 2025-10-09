from typing import Dict, List

from DALLib.IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter
from DALLib.Scripting.stsc2_commands import Command, CommandArgType, DALRDCommands
from DALLib.Scripting.stsc2_node import STSC2Node


class STSC2Sequence:
    def __init__(self) -> None:
        self.lines: List[Command] = []

    def read_sequence(self, reader: ExtendedBinaryReader, include_cmd_line_info: bool) -> None:
        commands_by_position: Dict[int, Command] = {}
        reader.offset = reader.get_length()

        while True:
            position = reader.get_position()
            cmd_line_info = reader.read_bytes(6) if include_cmd_line_info else None
            opcode = reader.read_byte()
            if opcode >= len(DALRDCommands):
                raise ValueError(f"Cmd read error. Read 0x{opcode:02X} at {reader.get_position() - 1:04X}.")

            template = DALRDCommands[opcode]
            line = template.read(reader, cmd_line_info)
            self.lines.append(line)
            commands_by_position[position] = line

            if reader.base_stream.tell() >= reader.offset:
                break

        for line in self.lines:
            if not line.argument_types:
                continue
            for index, arg_type in enumerate(line.argument_types):
                if arg_type == CommandArgType.COMMAND_REF:
                    reference = line.arguments[index]
                    if isinstance(reference, int) and reference in commands_by_position:
                        line.arguments[index] = commands_by_position[reference]

    def write_sequence(self, writer: ExtendedBinaryWriter, include_cmd_line_info: bool) -> None:
        line_positions: Dict[Command, int] = {}
        string_table: List[str] = []
        written_strings: Dict[str, int] = {}
        node_string_offsets: Dict[STSC2Node, int] = {}
        nodes: List[STSC2Node] = []

        for line in self.lines:
            line_positions[line] = writer.base_stream.tell()
            line.write(writer, string_table, nodes, DALRDCommands)

        for line in self.lines:
            if not line.argument_types:
                continue
            for index, arg_type in enumerate(line.argument_types):
                if arg_type == CommandArgType.COMMAND_REF:
                    ref_line = line.arguments[index]
                    if isinstance(ref_line, Command) and ref_line in line_positions:
                        key = f"{id(line)}_{id(ref_line)}"
                        writer.fill_in_offset(key, line_positions[ref_line])

        for node in nodes:
            if isinstance(node.Value, str) and node not in node_string_offsets:
                node_string_offsets[node] = writer.base_stream.tell()
                writer.write_null_terminated_string(node.Value)

        for index, text in enumerate(string_table):
            text_value = text or ""
            if text_value in written_strings:
                writer.fill_in_offset(f"str{index}", written_strings[text_value])
            else:
                position = writer.base_stream.tell()
                written_strings[text_value] = position
                writer.fill_in_offset(f"str{index}", position)
                writer.write_null_terminated_string(text_value)

        for index, node in enumerate(nodes):
            writer.fill_in_offset(f"node{index}")
            if isinstance(node.Value, str):
                node.write(writer, node_string_offsets[node])
            else:
                node.write(writer, 0)

        writer.fix_padding(0x10)
