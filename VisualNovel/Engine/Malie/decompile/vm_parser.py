import re
import struct
from io import BytesIO
from typing import Dict, List

from data_classes import (
    BaseCommand,
    ByteArgumentCommand,
    CallCommand,
    Chapter,
    ChapterString,
    ChapterStringConfig,
    CommandType,
    FunctionItem,
    JmpCommand,
    LabelItem,
    LineItem,
    NoArgumentCommand,
    PushStringCommand,
    StringItem,
    StringTag,
    UIntArgumentCommand,
    VarItem,
)


class VMParser:
    def __init__(self, data: bytes):
        self.reader = BytesIO(data)

        self.magic: int = 0
        self.vm_data_offset: int = 0
        self.vm_data_length: int = 0
        self.vm_code_offset: int = 0
        self.vm_code_length: int = 0

        self.vars: List[VarItem] = []
        self.functions: List[FunctionItem] = []
        self.functions_by_name: Dict[str, FunctionItem] = {}
        self.functions_by_id: Dict[int, FunctionItem] = {}
        self.labels: List[LabelItem] = []
        self.labels_by_name: Dict[str, LabelItem] = {}
        self.data_strings: List[StringItem] = []
        self.data_strings_by_offset: Dict[int, StringItem] = {}
        self.chapters: List[Chapter] = []
        self.commands: List[BaseCommand] = []
        self.commands_table: Dict[int, BaseCommand] = {}
        self.strings: List[LineItem] = []
        self.disasm: List[str] = []

        self.command_names = {
            CommandType.JMP: "jmp",
            CommandType.JNZ: "jnz",
            CommandType.JZ: "jz",
        }

        self._parse()

    def _read_uint32(self) -> int:
        return struct.unpack("<I", self.reader.read(4))[0]

    def _read_uint16(self) -> int:
        return struct.unpack("<H", self.reader.read(2))[0]

    def _read_byte(self) -> int:
        return struct.unpack("B", self.reader.read(1))[0]

    def _read_string(self) -> str:
        start = self.reader.tell()

        while self._read_uint16() != 0:
            pass

        end = self.reader.tell()
        self.reader.seek(start)

        # Read and decode
        length = end - start
        data = self.reader.read(length)
        text = data.decode("utf-16-le")
        text = text.rstrip("\x00")

        # Handle special [NAME] marker
        if text == "\a\f\x01":
            text = "[NAME]" + self._read_string()

        return text

    def _read_vars(self):
        count = self._read_uint32()
        self.vars = []

        for _ in range(count):
            # Read name length with flag
            length = self._read_uint32()
            if (length >> 24) != 0x80:
                raise ValueError("Invalid variable name length flag")

            length &= 0x7FFFFFFF
            name_bytes = self.reader.read(length)
            name = name_bytes.decode("utf-16-le").rstrip("\x00")

            # Read parameters
            parameters = []
            while True:
                flag = self._read_uint32()
                parameters.append(flag)
                if flag == 0:
                    break
                value = self._read_uint32()
                parameters.append(value)

            # Read additional 4 uint32 values
            for _ in range(4):
                parameters.append(self._read_uint32())

            self.vars.append(VarItem(name, parameters))

    def _read_functions(self):
        self.magic = self._read_uint32()
        count = self._read_uint32()

        self.functions = []
        self.functions_by_name = {}
        self.functions_by_id = {}

        for _ in range(count):
            # Read name length with flag
            length = self._read_uint32()
            if (length >> 24) != 0x80:
                raise ValueError("Invalid function name length flag")

            length &= 0x7FFFFFFF
            name_bytes = self.reader.read(length)
            name = name_bytes.decode("utf-16-le").rstrip("\x00")

            func_id = self._read_uint32()
            reserved0 = self._read_uint32()
            vm_code_offset = self._read_uint32()

            func = FunctionItem(name, func_id, reserved0, vm_code_offset)
            self.functions.append(func)
            self.functions_by_name[name] = func
            self.functions_by_id[func_id] = func

    def _read_labels(self):
        count = self._read_uint32()

        self.labels = []
        self.labels_by_name = {}

        for _ in range(count):
            # Read name length with flag
            length = self._read_uint32()
            if (length >> 24) != 0x80:
                raise ValueError("Invalid label name length flag")

            length &= 0x7FFFFFFF
            name_bytes = self.reader.read(length)
            name = name_bytes.decode("utf-16-le").rstrip("\x00")

            vm_code_offset = self._read_uint32()

            label = LabelItem(name, vm_code_offset)
            self.labels.append(label)
            self.labels_by_name[name] = label

    def _read_vm_data(self):
        self.vm_data_length = self._read_uint32()
        self.vm_data_offset = self.reader.tell()
        # Skip data for now, will read strings on-demand
        self.reader.seek(self.vm_data_offset + self.vm_data_length)

    def _read_data_string(self, offset: int) -> StringItem:
        local_offset = offset - self.vm_data_offset

        # Check if already read
        if local_offset in self.data_strings_by_offset:
            return self.data_strings_by_offset[local_offset]

        # Save position and seek to string
        save_pos = self.reader.tell()
        self.reader.seek(offset)

        # Read string
        text = self._read_string()
        string_item = StringItem(text, local_offset)

        # Restore position
        self.reader.seek(save_pos)

        # Cache and return
        self.data_strings_by_offset[local_offset] = string_item
        self.data_strings.append(string_item)

        return string_item

    def _parse_jmp_table(self, jmp_table: List[int], end: int, vm_stack: List[int], jumps: List):
        malie_end = self.functions_by_name["MALIE_END"].id

        while self.reader.tell() != end:
            offset = self.reader.tell() - self.vm_code_offset
            command = self._parse_command(vm_stack, jumps)
            command.offset = offset
            self.commands_table[offset] = command
            self.commands.append(command)

            if command.type == CommandType.CALL_UINT_NO_PARAM:
                if hasattr(command, "function") and command.function.id == malie_end:
                    break
            elif command.type == CommandType.JMP:
                if hasattr(command, "target_offset"):
                    jmp_table.append(command.target_offset)

    def _parse_command(self, vm_stack: List[int], jumps: List) -> BaseCommand:
        code = self._read_byte()
        command_type = CommandType(code)

        # Jump commands
        if command_type in (CommandType.JMP, CommandType.JNZ, CommandType.JZ):
            target = self._read_uint32()
            command = JmpCommand(0, command_type, target)
            jumps.append(command)
            self.disasm.append(f"{self.command_names[command_type]} to {target:X}")
            return command

        # CALL with uint ID
        elif command_type == CommandType.CALL_UINT_ID:
            func_id = self._read_uint32()
            arg = self._read_byte()
            if func_id not in self.functions_by_id:
                raise ValueError(f"Function with Id {func_id} not found")
            function = self.functions_by_id[func_id]
            self.disasm.append(f"CallUint  {function.name} {arg:X}")
            return CallCommand(0, command_type, function, arg)

        # CALL with byte ID
        elif command_type == CommandType.CALL_BYTE_ID:
            func_id = self._read_byte()
            arg = self._read_byte()
            if func_id not in self.functions_by_id:
                raise ValueError(f"Function with Id {func_id} not found")
            function = self.functions_by_id[func_id]
            self.disasm.append(f"CallByte  {function.name} {arg:X}")
            return CallCommand(0, command_type, function, arg)

        # No-argument commands
        elif command_type == CommandType.MASK_VEIP:
            self.disasm.append("Mask vEIP")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.PUSH_R32:
            self.disasm.append("PUSH_R32")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.POP_R32:
            self.disasm.append("POP_R32")
            if vm_stack:
                vm_stack.pop()
            return NoArgumentCommand(0, command_type)

        # Push int32/uint32
        elif command_type in (CommandType.PUSH_INT32, CommandType.PUSH_UINT32):
            value = self._read_uint32()
            vm_stack.append(value | 0x80000000)
            self.disasm.append(f"PUSH_INT32 {value:X}")
            return UIntArgumentCommand(0, command_type, value)

        # Push string commands
        elif command_type == CommandType.PUSH_STR_BYTE:
            offset = self._read_byte()
            full_offset = offset + self.vm_data_offset
            string_item = self._read_data_string(full_offset)
            vm_stack.append(full_offset)
            self.disasm.append(f"PUSH_STR_BYTE {string_item.text}")
            return PushStringCommand(0, command_type, string_item)

        elif command_type == CommandType.PUSH_STR_SHORT:
            offset = self._read_uint16()
            full_offset = offset + self.vm_data_offset
            string_item = self._read_data_string(full_offset)
            vm_stack.append(full_offset)
            self.disasm.append(f"PUSH_STR_SHORT {string_item.text}")
            return PushStringCommand(0, command_type, string_item)

        elif command_type == CommandType.PUSH_STR_INT:
            offset = self._read_uint32()
            full_offset = offset + self.vm_data_offset
            string_item = self._read_data_string(full_offset)
            vm_stack.append(full_offset)
            self.disasm.append(f"PUSH_STR_INT {string_item.text}")
            return PushStringCommand(0, command_type, string_item)

        elif command_type == CommandType.NONE:
            self.disasm.append("NONE")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.POP:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("POP")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.PUSH_0:
            vm_stack.append(0 | 0x80000000)
            self.disasm.append("PUSH_0")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.UNKNOWN_1:
            self.disasm.append("UNKNOWN1")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.PUSH_0x:
            arg = self._read_byte()
            vm_stack.append(arg | 0x80000000)
            self.disasm.append(f"PUSH_0x{arg:X}")
            return ByteArgumentCommand(0, command_type, arg)

        elif command_type == CommandType.PUSH_SP:
            self.disasm.append("PUSH_SP")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.NEG:
            self.disasm.append("NEG")
            return NoArgumentCommand(0, command_type)

        # Arithmetic operations
        elif command_type == CommandType.ADD:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ADD")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.SUB:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("SUB")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.MUL:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("MUL")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.DIV:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("DIV")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.MOD:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("MOD")
            return NoArgumentCommand(0, command_type)

        # Logical operations
        elif command_type == CommandType.AND:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("AND")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.OR:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("OR")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.XOR:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("XOR")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.BOOL1:
            self.disasm.append("BOOL1")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.BOOL2:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("BOOL2")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.BOOL3:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("BOOL3")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.BOOL4:
            self.disasm.append("BOOL4")
            return NoArgumentCommand(0, command_type)

        # Comparison operations
        elif command_type == CommandType.ISL:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ISL")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.ISLE:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ISLE")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.ISNLE:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ISNLE")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.ISNL:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ISNL")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.ISEQ:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ISEQ")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.ISNEQ:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("ISNEQ")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.SHL:
            self.disasm.append("SHL")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.SAR:
            if vm_stack:
                vm_stack.pop()
            self.disasm.append("SAR")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.INC:
            self.disasm.append("INC")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.DEC:
            self.disasm.append("DEC")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.ADD_REG:
            self.disasm.append("ADD_REG")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.DEBUG:
            self.disasm.append("DEBUG")
            return NoArgumentCommand(0, command_type)

        # CALL without parameters
        elif command_type == CommandType.CALL_UINT_NO_PARAM:
            func_id = self._read_uint32()
            vm_stack.append(func_id | 0x80000000)
            if func_id not in self.functions_by_id:
                raise ValueError(f"Function with Id {func_id} not found")
            function = self.functions_by_id[func_id]
            self.disasm.append(f"CallUint  {function.name}")
            return CallCommand(0, command_type, function)

        elif command_type == CommandType.ADD_2:
            self.disasm.append("ADD_2")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.FPCOPY:
            self.disasm.append("FPCOPY")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.FPGET:
            self.disasm.append("FPGET")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.INITSTACK:
            value = self._read_uint32()
            self.disasm.append(f"INITSTACK {value}")
            return UIntArgumentCommand(0, command_type, value)

        elif command_type == CommandType.Unknown2:
            self.disasm.append("Unknown2")
            return NoArgumentCommand(0, command_type)

        elif command_type == CommandType.RET:
            temp = self._read_byte()
            self.disasm.append("RET")
            return ByteArgumentCommand(0, command_type, temp)

        else:
            raise ValueError(f"Unknown command type: {code:02X}")

    def _read_code(self) -> List[ChapterStringConfig]:
        self.vm_code_length = self._read_uint32()
        self.data_strings = []
        self.data_strings_by_offset = {}
        self.vm_code_offset = self.reader.tell()
        end = self.reader.tell() + self.vm_code_length
        self.disasm = []

        moji = []
        scenario_offset = self.functions_by_name["maliescenario"].vm_code_offset

        # Get function IDs
        ms_message = self.functions_by_name["_ms_message"].id
        malie_name = self.functions_by_name["MALIE_NAME"].id
        malie_lable = self.functions_by_name["MALIE_LABLE"].id
        tag = self.functions_by_name["tag"].id
        frame_layer_send_message = self.functions_by_name["FrameLayer_SendMessage"].id
        system_get_result = self.functions_by_name["System_GetResult"].id

        chapter_names = []
        chapter_indices = []
        current_moji = ChapterStringConfig()
        jmp_table = []
        select_table = []
        jmp_iterator_index = -1

        self.commands = []
        self.commands_table = {}
        vm_stack = []
        p_last_string = None
        jumps = []

        while self.reader.tell() != end:
            offset = self.reader.tell() - self.vm_code_offset
            command = self._parse_command(vm_stack, jumps)
            command.offset = offset
            self.commands_table[offset] = command
            self.commands.append(command)

            # After scenario start
            if offset > scenario_offset:
                # Check chapter boundaries from jump table
                if jmp_table and jmp_iterator_index != len(jmp_table):
                    if jmp_iterator_index >= 0 and offset > jmp_table[jmp_iterator_index]:
                        jmp_iterator_index += 1
                        chapter_indices.append(len(moji))

                # Process commands
                if command.type in (CommandType.CALL_UINT_NO_PARAM, CommandType.CALL_BYTE_ID, CommandType.CALL_UINT_ID):
                    if hasattr(command, "function"):
                        func_id = command.function.id

                        # Check for tag (chapter markers)
                        if func_id == tag and p_last_string:
                            match = re.search(r"<chapter name='(.*?)'>", p_last_string.text)
                            if match:
                                p_last_string.tag = StringTag.CHAPTER
                                chapter_names.append(match.group(1))
                                chapter_indices.append(len(moji))

                        # Check for message
                        elif func_id == ms_message:
                            if vm_stack:
                                vm_stack.pop()
                            if vm_stack:
                                current_moji.index = vm_stack[-1] & ~0x80000000
                            vm_stack.clear()
                            vm_stack.append(0)
                            moji.append(current_moji)
                            current_moji = ChapterStringConfig()
                            select_table.clear()

                        # Check for name
                        elif func_id == malie_name and p_last_string:
                            current_moji.name = p_last_string.text
                            p_last_string.tag = StringTag.NAME

                        # Check for label (jump table)
                        elif func_id == malie_lable and len(moji) == 0 and p_last_string:
                            if p_last_string.text == "_index":
                                p_last_string.tag = StringTag.LABEL
                                self._parse_jmp_table(jmp_table, end, vm_stack, jumps)
                                jmp_iterator_index = 0
                                continue

                        # Check for selections
                        elif func_id == system_get_result:
                            for x in select_table:
                                # old = [1644342, 1644348, 1644364, 2147483748]
                                # new = [2147483648, 114952, 114980, 115008, 51184]
                                if x < 0x80000000:
                                    s = self._read_data_string(x)
                                    s.tag = StringTag.SELECT

                        elif func_id == frame_layer_send_message and len(vm_stack) > 4:
                            for _ in range(4):
                                if vm_stack:
                                    vm_stack.pop()
                            if vm_stack:
                                loc = vm_stack[-1]
                                if loc > 0:
                                    select_table.append(loc)

                # Update last string reference
                if isinstance(command, PushStringCommand):
                    p_last_string = command.string_item

        # Resolve jump targets
        for jump in jumps:
            offset = jump.command_offset & 0xFFFFFF
            if offset not in self.commands_table:
                raise ValueError("Command ptr incorrect")
            jump.target_command = self.commands_table[offset]

        # Resolve function command pointers
        for function in self.functions:
            if function.vm_code_offset not in self.commands_table:
                raise ValueError("Function command ptr incorrect")
            function.command = self.commands_table[function.vm_code_offset]

        # Resolve label command pointers
        for label in self.labels:
            if label.vm_code_offset not in self.commands_table:
                raise ValueError("Label command ptr incorrect")
            label.command = self.commands_table[label.vm_code_offset]

        return moji, chapter_names, chapter_indices

    def _read_strings(self):
        print("strings count addr", self.reader.tell())
        count = self._read_uint32()
        ranges = []

        for _ in range(count):
            start = struct.unpack("<i", self.reader.read(4))[0]
            length = struct.unpack("<i", self.reader.read(4))[0]
            ranges.append((start, length))

        table_length = self._read_uint32()
        start_offset = self.reader.tell()

        self.strings = []
        for start, length in ranges:
            self.reader.seek(start_offset + start)
            data = self.reader.read(length)
            text = data.decode("utf-16-le")

            line_item = self._parse_line_item(text)
            self.strings.append(line_item)

    def _parse_line_item(self, line: str) -> LineItem:
        # Replace [NAME] marker
        line = line.replace("\a\f\x01\x00", "[NAME]")

        # Check for voice marker
        voice = None
        voice_match = re.match(r"\a\x08(?P<voice>v_[^\x00]+)\x00(?P<content>.*)", line, re.DOTALL)
        if voice_match:
            voice = voice_match.group("voice")
            line = voice_match.group("content")

        # Extract end characters
        end_chars = ["\t", "\r", "\a", "\b", "\x00", "\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07"]
        start_pos = len(line) - 1
        while start_pos >= 0 and line[start_pos] in end_chars:
            start_pos -= 1

        if start_pos != len(line) - 1:
            end = line[start_pos + 1 :]
            line = line[: start_pos + 1]
        else:
            end = ""

        # Split into text items
        texts = [StringItem(text, 0) for text in line.split("\n")]

        return LineItem(voice, texts, end)

    def _create_chapters(self, moji: List[ChapterStringConfig], chapter_names: List[str], chapter_indices: List[int]):
        chapter_indices.append(len(moji))
        chapters = []

        for i in range(len(chapter_names)):
            start_idx = chapter_indices[i]
            end_idx = chapter_indices[i + 1]
            title = chapter_names[i]

            lines = []
            for j in range(start_idx, end_idx):
                name = moji[j].name
                text = self.strings[moji[j].index]
                lines.append(ChapterString(name, text))

            chapters.append(Chapter(title, lines, start_idx, end_idx))

        self.chapters = chapters

    def _parse(self):
        self._read_vars()
        self._read_functions()
        self._read_labels()
        self._read_vm_data()
        moji, chapter_names, chapter_indices = self._read_code()
        self._read_strings()
        self._create_chapters(moji, chapter_names, chapter_indices)

        # Sort data strings by offset
        self.data_strings.sort(key=lambda x: x.offset)
