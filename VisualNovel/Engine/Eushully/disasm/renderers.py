import json
from abc import ABC, abstractmethod
from typing import Any

from age_shared import Header, Instruction, get_type_label, is_control_flow, is_label_argument
from ir import IR
from overflow import u32


class Renderer(ABC):
    @abstractmethod
    def render(self, ir: IR) -> str:
        pass


class TextRenderer(Renderer):
    def render(self, ir: IR) -> str:
        output = self._render_header(ir.header)

        for instruction in ir.instructions:
            # Add label if this instruction is a target
            if instruction.offset in ir.labels:
                label_addr = ir.header.length + u32(instruction.offset << 2)
                output += f"\nlabel_{label_addr:08x}\n"

            output += self._render_instruction(ir.header, instruction)

        return output

    def _render_header(self, header: Header) -> str:
        hdr = header.header
        result = "==Binary Information - do not edit==\n"
        result += f"signature = {hdr.signature.decode('utf-8', errors='replace')}\n"
        result += f"local_vars = {{ {hdr.local_integer_1:x} {hdr.local_floats:x} {hdr.local_strings_1:x} {hdr.local_integer_2:x} {hdr.unknown_data:x} {hdr.local_strings_2:x} }}\n"
        result += "====\n\n"
        return result

    def _render_instruction(self, header: Header, instruction: Instruction) -> str:
        result = instruction.definition.label

        if instruction.arguments:
            result += " "
            arg_strs = []

            for idx, arg in enumerate(instruction.arguments):
                type_label = get_type_label(arg.arg_type)

                if type_label:
                    # Typed argument: (local-int 5)
                    arg_strs.append(f"({type_label} {arg.raw_data:x})")
                elif arg.arg_type == 2:
                    # String: "text"
                    arg_strs.append(f'"{arg.decoded_string}"')
                elif instruction.definition.op_code == 0x64 and arg.arg_type == 0 and idx == 1:
                    # Array: [1 2 3 4]
                    array_str = " ".join(f"{v:x}" for v in arg.data_array)
                    arg_strs.append(f"[{array_str}]")
                elif is_control_flow(instruction) and is_label_argument(instruction, idx):
                    # Label reference: label_00001234
                    label_addr = header.length + u32(arg.raw_data << 2)
                    arg_strs.append(f"label_{label_addr:08x}")
                else:
                    # Raw hex value
                    arg_strs.append(f"{arg.raw_data:x}")

            result += " ".join(arg_strs)

        result += "\n"
        return result


class JsonRenderer(Renderer):
    def __init__(self, indent: int = 2):
        self.indent = indent

    def render(self, ir: IR) -> str:
        data = {"header": self._serialize_header(ir.header), "instructions": self._group_instructions_by_label(ir)}
        return json.dumps(data, indent=self.indent, ensure_ascii=False)

    def _group_instructions_by_label(self, ir: IR) -> dict[str, list[dict[str, Any]]]:
        grouped = {}
        current_label = "__entry__"
        current_group = []

        for instruction in ir.instructions:
            # Check if this instruction has a label
            if instruction.offset in ir.labels:
                # Save previous group if it has instructions
                if current_group:
                    grouped[current_label] = current_group

                # Start new group with this label
                label_addr = ir.header.length + u32(instruction.offset << 2)
                current_label = f"label_{label_addr:08x}"
                current_group = []

            # Add instruction to current group
            current_group.append(self._serialize_instruction(ir.header, instruction))

        # Save the last group
        if current_group:
            grouped[current_label] = current_group

        return grouped

    def _serialize_header(self, header: Header) -> dict[str, Any]:
        hdr = header.header
        return {
            "signature": hdr.signature.decode("utf-8", errors="replace"),
            "is_ver5": header.is_ver5,
            "length": header.length,
            "local_vars": {
                "local_integer_1": hdr.local_integer_1,
                "local_floats": hdr.local_floats,
                "local_strings_1": hdr.local_strings_1,
                "local_integer_2": hdr.local_integer_2,
                "unknown_data": hdr.unknown_data,
                "local_strings_2": hdr.local_strings_2,
            },
            "tables": {
                "table_1_offset": hdr.table_1_offset,
                "table_2_offset": hdr.table_2_offset,
                "table_3_offset": hdr.table_3_offset,
            },
        }

    def _serialize_instruction(self, header: Header, instruction: Instruction) -> dict[str, Any]:
        return {
            "offset": instruction.offset,
            "address": header.length + u32(instruction.offset << 2),
            "opcode": instruction.definition.op_code,
            "label": instruction.definition.label,
            "arguments": [self._serialize_argument(header, instruction, idx, arg) for idx, arg in enumerate(instruction.arguments)],
        }

    def _serialize_argument(self, header: Header, instruction: Instruction, idx: int, arg) -> dict[str, Any]:
        result = {"type": arg.arg_type, "raw_data": arg.raw_data}

        type_label = get_type_label(arg.arg_type)
        if type_label:
            result["type_label"] = type_label

        if arg.arg_type == 2:
            result["string"] = arg.decoded_string

        if instruction.definition.op_code == 0x64 and arg.arg_type == 0 and idx == 1:
            result["array"] = arg.data_array

        if is_control_flow(instruction) and is_label_argument(instruction, idx):
            label_addr = header.length + u32(arg.raw_data << 2)
            result["label_ref"] = f"label_{label_addr:08x}"
            result["label_address"] = label_addr

        return result
