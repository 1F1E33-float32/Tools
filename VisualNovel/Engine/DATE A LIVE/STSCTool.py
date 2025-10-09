import argparse
from pathlib import Path
from typing import Dict, List

from DALLib.Exceptions import STSCDisassembleException
from DALLib.File import STSCFile
from DALLib.Scripting import (
    ArgumentType,
    ComparisonOperators,
    DALRRInstructions,
    Instruction,
    InstructionIf,
    InstructionSwitch,
    STSCMacros,
)


class STSCTextHandler:
    comparison_operator_strings = ["==", "!=", "<=", "<", ">=", ">", "!= 0", "== 0"]

    @staticmethod
    def place_line(
        file: STSCFile,
        strings: List[str],
        lines: List[int],
        address: int,
        text: str,
    ) -> None:
        index = file.find_index(address)
        strings.insert(lines[index], text)
        for i in range(index, len(lines)):
            lines[i] += 1

    @staticmethod
    def convert_single_instruction_to_text(
        file: STSCFile,
        instruction_pointer: int,
        labels: Dict[str, int],
        scope_ends: List[int],
        lines: List[int],
        strings: List[str],
        address: int,
        current_indent: int,
    ) -> int:
        instruction = file.instructions[instruction_pointer]
        while scope_ends and scope_ends[-1] == address:
            scope_ends.pop()
            current_indent -= 1
            strings.append(" " * (current_indent * 4) + "}")

        indent_prefix = " " * (current_indent * 4)

        if any(value == address for value in labels.values()):
            name = next(key for key, value in labels.items() if value == address)
            strings.append(f"#label {name}")

        if instruction.name == "if":
            lines.append(len(strings))
            if_instruction = instruction
            comparisons = [STSCTextHandler.convert_comparison_to_string(comparison) for comparison in if_instruction.comparisons]
            strings.append(f"{indent_prefix}if ({' && '.join(comparisons)})")
            strings.append(f"{indent_prefix}{{")
            current_indent += 1
            scope_ends.append(if_instruction.get_argument(0))
        else:
            arg_strings = []
            for index, arg in enumerate(instruction.arguments):
                arg_type = instruction.arg_types[index]
                if arg_type == ArgumentType.AT_CodePointer:
                    jump_address = instruction.get_argument(index)
                    label_name = f"SUB_{jump_address:04X}" if instruction.name == DALRRInstructions[0x1A].name else f"LABEL_{jump_address:04X}"
                    if label_name not in labels:
                        labels[label_name] = jump_address
                        if file.find_index(jump_address) < instruction_pointer:
                            STSCTextHandler.place_line(file, strings, lines, jump_address, f"#label {label_name}")
                    arg_strings.append(label_name)
                else:
                    arg_strings.append(STSCTextHandler.convert_argument_to_string(instruction, index))

            if instruction.name == DALRRInstructions[0x52].name:
                try:
                    character_index = int(arg_strings[0])
                    macro_value = STSCMacros.DALRRCharacterNames[character_index]
                    if macro_value:
                        arg_strings[0] = macro_value
                except (ValueError, IndexError):
                    pass

            lines.append(len(strings))
            strings.append(f"{indent_prefix}{instruction.name}({', '.join(arg_strings)})")

        return current_indent

    @staticmethod
    def convert_to_text(file: STSCFile) -> List[str]:
        labels: Dict[str, int] = {}
        header_address = 0x0E if file.version == 4 else 0x3C
        strings: List[str] = [f"#scriptID 0x{file.script_id:08X}", f"#scriptName {file.script_name}"]
        scope_ends: List[int] = []
        lines: List[int] = []
        current_indent = 0
        address = header_address

        for instruction_pointer in range(len(file.instructions)):
            current_indent = STSCTextHandler.convert_single_instruction_to_text(
                file,
                instruction_pointer,
                labels,
                scope_ends,
                lines,
                strings,
                address,
                current_indent,
            )
            instruction = file.instructions[instruction_pointer]
            address += instruction.get_instruction_size()

        while current_indent != 0:
            current_indent -= 1
            strings.append(" " * (current_indent * 4) + "}")
            if scope_ends:
                scope_ends.pop()

        return strings

    @staticmethod
    def convert_to_object(file: STSCFile, text: List[str]) -> None:
        labels: Dict[str, int] = {}
        scopes: List[int] = []
        scope_id = 0
        base_address = 0x0E if file.version == 4 else 0x3C
        address = base_address

        for index, raw_line in enumerate(text):
            line = raw_line.strip()
            if not line:
                continue

            first_char = line[0]
            if first_char == "#":
                if line.startswith("#label"):
                    labels[line[7:]] = address
                elif line.startswith("#scriptID"):
                    file.script_id = int(STSCTextHandler.process_literals(line[10:]), 0)
                elif line.startswith("#scriptName"):
                    file.script_name = line[12:]
                continue

            if first_char == "{":
                continue
            if first_char == "}":
                if scopes:
                    label_key = str(scopes.pop())
                    labels[label_key] = address
                continue

            tokens = STSCTextHandler.parse_code_line(raw_line)
            if not tokens:
                continue

            name = tokens[0]
            base_instruction = next((instr for instr in DALRRInstructions if instr and instr.name == name), None)
            if base_instruction is None:
                raise ValueError(f"Error: Could not find any instructions for '{name}'! Please check line {index}.")

            if name == "if":
                instruction = InstructionIf()
                instruction.arguments.append(str(scope_id))
                scopes.append(scope_id)
                scope_id += 1
                comparison_strings = [part.strip() for part in tokens[1].split("&&") if part.strip()]
                for comp in comparison_strings:
                    for operator in STSCTextHandler.comparison_operator_strings:
                        if operator in comp:
                            parts = comp.split(operator)
                            left_literal = STSCTextHandler._parse_numeric_literal(parts[0], bits=32, signed=False)
                            right_src = parts[1] if len(parts) > 1 else "0"
                            right_literal = STSCTextHandler._parse_numeric_literal(right_src, bits=32, signed=False)
                            comparison = InstructionIf.Comparison(left_literal & 0xFFFFFFFF, ComparisonOperators(STSCTextHandler.comparison_operator_strings.index(operator)), right_literal & 0xFFFFFFFF)
                            instruction.comparisons.append(comparison)
                            break
                file.instructions.append(instruction)
                address += instruction.get_instruction_size()
            elif name == "switch":
                instruction = InstructionSwitch("switch", None)
                unknown = STSCTextHandler._parse_numeric_literal(tokens[1], bits=32, signed=False)
                amount = STSCTextHandler._parse_numeric_literal(tokens[2], bits=16, signed=False)
                end_flag = tokens[3].lower() == "true"

                arg_types = [ArgumentType.AT_DataReference, ArgumentType.AT_Int16, ArgumentType.AT_Bool]
                arguments = [unknown, amount, end_flag]

                for i in range(amount):
                    case_value = STSCTextHandler._parse_numeric_literal(tokens[4 + i * 2], bits=32, signed=True)
                    destination = tokens[4 + i * 2 + 1]
                    arg_types.extend([ArgumentType.AT_Int32, ArgumentType.AT_CodePointer])
                    arguments.append(case_value)
                    arguments.append(destination)

                instruction.arg_types = arg_types
                instruction.arguments = arguments
                file.instructions.append(instruction)
                address += instruction.get_instruction_size()
            else:
                arg_types = list(base_instruction.arg_types) if base_instruction.arg_types else None
                instruction = Instruction(base_instruction.name, arg_types)
                if instruction.arg_types:
                    for arg_type, token in zip(instruction.arg_types, tokens[1:]):
                        STSCTextHandler.add_argument(instruction, arg_type, token)
                file.instructions.append(instruction)
                address += instruction.get_instruction_size()

        for instruction in file.instructions:
            if not instruction.arg_types:
                continue
            for idx, arg_type in enumerate(instruction.arg_types):
                if arg_type == ArgumentType.AT_CodePointer and isinstance(instruction.arguments[idx], str) and instruction.arguments[idx] in labels:
                    instruction.arguments[idx] = labels[instruction.arguments[idx]]

    @staticmethod
    def convert_argument_to_string(instruction: Instruction, index: int) -> str:
        arg_type = instruction.arg_types[index]
        value = instruction.get_argument(index)
        if arg_type == ArgumentType.AT_Bool:
            return "true" if value else "false"
        if arg_type == ArgumentType.AT_Float:
            return f"{float(value)}f"
        if arg_type in (ArgumentType.AT_String, ArgumentType.AT_StringPtr):
            if value is None:
                return "null"
            escaped = str(value).replace('"', '\\"')
            return f'"{escaped}"'
        if arg_type == ArgumentType.AT_DataReference:
            return STSCTextHandler._format_data_reference(int(value))
        if arg_type in (ArgumentType.AT_Byte, ArgumentType.AT_Int16, ArgumentType.AT_Int32, ArgumentType.AT_CodePointer):
            return STSCTextHandler._format_int(value)
        return str(value)

    @staticmethod
    def add_argument(instruction: Instruction, arg_type: ArgumentType, token: str) -> None:
        if arg_type == ArgumentType.AT_Bool:
            instruction.arguments.append(token.lower() != "false")
        elif arg_type == ArgumentType.AT_Byte:
            instruction.arguments.append(STSCTextHandler._parse_numeric_literal(token, bits=8, signed=False))
        elif arg_type == ArgumentType.AT_Int16:
            instruction.arguments.append(STSCTextHandler._parse_numeric_literal(token, bits=16, signed=True))
        elif arg_type == ArgumentType.AT_Int32:
            instruction.arguments.append(STSCTextHandler._parse_numeric_literal(token, bits=32, signed=True))
        elif arg_type == ArgumentType.AT_CodePointer:
            instruction.arguments.append(token)
        elif arg_type == ArgumentType.AT_DataReference:
            instruction.arguments.append(STSCTextHandler._parse_numeric_literal(token, bits=32, signed=False))
        elif arg_type == ArgumentType.AT_Float:
            literal = STSCTextHandler.process_literals(token)
            instruction.arguments.append(float(literal))
        elif arg_type in (ArgumentType.AT_String, ArgumentType.AT_StringPtr):
            instruction.arguments.append(token)

    @staticmethod
    def convert_comparison_to_string(comparison: InstructionIf.Comparison) -> str:
        left = comparison.left
        right = comparison.right
        left_str = STSCTextHandler._format_int(left)
        right_str = STSCTextHandler._format_int(right)
        op = STSCTextHandler.comparison_operator_strings[comparison.operator.value]
        if comparison.operator not in (ComparisonOperators.NotZero, ComparisonOperators.Zero):
            return f"{left_str} {op} {right_str}"
        return f"{left_str} {op}"

    @staticmethod
    def parse_code_line(code_line: str) -> List[str]:
        inside_string = False
        escaped = False
        buffer = []
        string_buffer = []
        tokens: List[str] = []
        i = 0
        length = len(code_line)

        while i < length:
            char = code_line[i]
            if char == "\\":
                escaped = True
            if escaped:
                if i + 1 < length and code_line[i + 1] != '"':
                    string_buffer.append(char)
                i += 1
                if i < length:
                    string_buffer.append(code_line[i])
                escaped = False
                i += 1
                continue

            if not inside_string and char == " ":
                i += 1
                continue

            if not inside_string and char == "(":
                if buffer:
                    tokens.append(STSCTextHandler.process_literals("".join(buffer)))
                    buffer = []
                i += 1
                continue

            if not inside_string and char == ")":
                if buffer:
                    tokens.append(STSCTextHandler.process_literals("".join(buffer)))
                    buffer = []
                i += 1
                continue

            if not inside_string and char == ",":
                if buffer:
                    tokens.append(STSCTextHandler.process_literals("".join(buffer)))
                    buffer = []
                i += 1
                continue

            if char == '"':
                if inside_string:
                    inside_string = False
                    buffer.extend(string_buffer)
                    string_buffer = []
                else:
                    inside_string = True
                i += 1
                continue

            if inside_string:
                string_buffer.append(char)
            else:
                buffer.append(char)
            i += 1

        if buffer:
            tokens.append(STSCTextHandler.process_literals("".join(buffer)))

        return tokens

    @staticmethod
    def process_literals(token: str, allow_float: bool = True) -> str:
        token = token.strip()
        if token in STSCMacros.DALRRCharacterNames:
            return str(STSCMacros.DALRRCharacterNames.index(token))
        if token.lower().startswith("0x"):
            try:
                return str(STSCTextHandler._parse_numeric_literal(token, bits=32, signed=True))
            except ValueError:
                return token
        if allow_float and token.lower().endswith("f"):
            try:
                return str(float(token[:-1]))
            except ValueError:
                return token
        return token.strip('"')

    @staticmethod
    def _format_int(value: int, bits: int = 32) -> str:
        value = int(value)
        if value > 2048 or value < -2048:
            mask = (1 << bits) - 1
            return f"0x{value & mask:X}"
        return str(value)

    @staticmethod
    def _format_data_reference(value: int) -> str:
        return f"0x{value & 0xFFFFFFFF:08X}"

    @staticmethod
    def _parse_numeric_literal(token: str, bits: int = 32, signed: bool = True) -> int:
        token = token.strip()
        try:
            index = STSCMacros.DALRRCharacterNames.index(token)
            return index & ((1 << bits) - 1)
        except ValueError:
            pass

        if token.lower().startswith("0x"):
            raw = token[2:]
            sign = 1
            if raw.startswith("-"):
                sign = -1
                raw = raw[1:]
            elif raw.startswith("+"):
                raw = raw[1:]
            raw_value = int(raw or "0", 16)
            value = raw_value * sign
            mask = (1 << bits) - 1
            if signed:
                value &= mask
                if value >= 1 << (bits - 1):
                    value -= 1 << bits
            else:
                value &= mask
            return value

        if token.lower().endswith("f"):
            token = token[:-1]

        try:
            value = int(token, 0)
        except ValueError:
            value = 0

        if signed:
            mask = (1 << bits) - 1
            value &= mask
            if value >= 1 << (bits - 1):
                value -= 1 << bits
        else:
            value &= (1 << bits) - 1
        return value


def _process_file(path: Path) -> None:
    file = STSCFile()
    if path.suffix.lower() == ".bin":
        try:
            file.load(str(path))
        except STSCDisassembleException as exc:
            print(f"Error: {exc}.")
            return
        text_lines = STSCTextHandler.convert_to_text(file)
        output_path = path.with_suffix(".txt")
        output_path.write_text("\n".join(text_lines), encoding="utf-8")
    elif path.suffix.lower() == ".txt":
        text_lines = path.read_text(encoding="utf-8").splitlines()
        STSCTextHandler.convert_to_object(file, text_lines)
        output_path = path.with_suffix(".bin")
        file.save(str(output_path))


def run_tool(input_directory: Path) -> None:
    STSCMacros.fill()
    if not input_directory.exists():
        raise FileNotFoundError(f"Input directory '{input_directory}' does not exist.")
    if not input_directory.is_dir():
        raise NotADirectoryError(f"Input path '{input_directory}' is not a directory.")

    for path in sorted(input_directory.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".bin"}:
            continue
        _process_file(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert STSC binary/text files.")
    parser.add_argument("input_directory", help="Directory containing .bin or .txt files")
    args = parser.parse_args()
    run_tool(Path(args.input_directory))
