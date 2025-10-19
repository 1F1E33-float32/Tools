import os
import struct
import sys
import unicodedata
from typing import List, Tuple

MAGIC_ESCR = b"ESCR1_00"

OPCODES = {
    0: ("END", 0, "Exit script execution"),
    1: ("JUMP", 0, "Unconditional jump (reads inline param)"),
    2: ("JUMPZ", 0, "Jump if zero (reads inline param)"),
    3: ("CALL", 0, "Call subroutine (reads inline param)"),
    4: ("RET", 0, "Return from subroutine"),
    5: ("PUSH", 0, "Push value (reads inline param)"),
    6: ("POP", 0, "Pop value from stack"),
    7: ("STR", 0, "Push string reference (reads inline param)"),
    8: ("SETVAR", 0, "Set variable"),
    9: ("GETVAR", 0, "Get variable"),
    10: ("SETFLAG", 0, "Set flag"),
    11: ("GETFLAG", 0, "Get flag"),
    12: ("NEG", 0, "Negate top of stack"),
    13: ("ADD", 0, "Addition"),
    14: ("SUB", 0, "Subtraction"),
    15: ("MUL", 0, "Multiplication"),
    16: ("DIV", 0, "Division"),
    17: ("MOD", 0, "Modulo"),
    18: ("NOT", 0, "Bitwise NOT"),
    19: ("AND", 0, "Bitwise AND"),
    20: ("OR", 0, "Bitwise OR"),
    21: ("XOR", 0, "Bitwise XOR"),
    22: ("SHR", 0, "Shift right"),
    23: ("SHL", 0, "Shift left"),
    24: ("EQ", 0, "Equal comparison"),
    25: ("NE", 0, "Not equal comparison"),
    26: ("GT", 0, "Greater than"),
    27: ("GE", 0, "Greater or equal"),
    28: ("LT", 0, "Less than"),
    29: ("LE", 0, "Less or equal"),
    30: ("LNOT", 0, "Logical NOT"),
    31: ("LAND", 0, "Logical AND"),
    32: ("LOR", 0, "Logical OR"),
    33: ("LINE", 0, "Set source line number (reads inline param)"),
}

RESERVE_COUNT = len(OPCODES)


PROC_COMMANDS = {
    0: ("END", 1, "End script"),
    1: ("JUMP", 1, "Jump to label"),
    2: ("CALL", 1, "Call script"),
    3: ("AUTOPLAY", 1, "Auto play mode"),
    4: ("FRAME", 1, "Set text frame"),
    5: ("TEXT", 2, "Show/hide text frame"),
    6: ("CLEAR", 1, "Clear text"),
    7: ("GAP", 2, "Text gap/spacing"),
    8: ("MES", 1, "Display message"),
    9: ("TLK", -1, "Talk: set character name, face, voice (name_id, face_id, param, voice_ids...)"),
    10: ("MENU", 3, "Show menu"),
    11: ("SELECT", 1, "Select option"),
    12: ("LSF_INIT", 1, "Init LSF"),
    13: ("LSF_SET", -1, "Set LSF"),
    14: ("LSF_GET", 2, "Get LSF"),
    15: ("LSF_BREAK", -1, "LSF break"),
    16: ("CG", -1, "Load CG"),
    17: ("CG_OPT", -1, "CG options"),
    18: ("CG_POS", 3, "CG position"),
    19: ("CG_SET", 3, "CG set"),
    20: ("CG_GET", 2, "CG get"),
    21: ("EM", 5, "Emotion/effect"),
    22: ("CLR", 1, "Clear layer"),
    23: ("DISP", 3, "Display"),
    24: ("PATH", -1, "Set path"),
    25: ("TRANS", 0, "Transition"),
    26: ("MOT_SET", 3, "Motion set"),
    27: ("MOT_GET", 2, "Motion get"),
    28: ("BGMPLAY", 3, "Play BGM"),
    29: ("BGMSTOP", 1, "Stop BGM"),
    30: ("BGMVOLUME", 2, "BGM volume"),
    31: ("BGMFX", 1, "BGM effect"),
    32: ("AMBPLAY", 3, "Play ambient"),
    33: ("AMBSTOP", 1, "Stop ambient"),
    34: ("AMBVOLUME", 2, "Ambient volume"),
    35: ("AMBFX", 1, "Ambient effect"),
    36: ("BGVPLAY", 3, "Play BGV"),
    37: ("BGVSTOP", 1, "Stop BGV"),
    38: ("BGVVOLUME", 2, "BGV volume"),
    39: ("BGVFX", 1, "BGV effect"),
    40: ("SEPLAY", 5, "Play sound effect"),
    41: ("SESTOP", 2, "Stop sound effect"),
    42: ("SEWAIT", 1, "Wait for SE"),
    43: ("SEVOLUME", 3, "SE volume"),
    44: ("SEFX", 1, "SE effect"),
    45: ("VOCPLAY", 4, "Play voice: (track, voice_id, fade_time, begin_time) ; voice_id = chr*65536 + idx"),
    46: ("VOCSTOP", 2, "Stop voice"),
    47: ("VOCWAIT", 1, "Wait for voice"),
    48: ("VOCVOLUME", 3, "Voice volume"),
    49: ("VOCFX", 1, "Voice effect"),
    50: ("QUAKE", 4, "Screen shake"),
    51: ("FLASH", 2, "Screen flash"),
    52: ("FILTER", 2, "Screen filter"),
    53: ("EFFECT", 1, "Screen effect"),
    54: ("SYNC", 2, "Synchronize"),
    55: ("WAIT", 1, "Wait"),
    56: ("MOVIE", 1, "Play movie"),
    57: ("CREDIT", 1, "Show credits"),
    58: ("EVENT", 1, "Trigger event"),
    59: ("SCENE", 1, "Change scene"),
    60: ("TITLE", 1, "Go to title"),
    61: ("NOTICE", 3, "Show notice"),
    62: ("SET_PASS", 2, "Set password"),
    63: ("IS_PASS", 1, "Check password"),
    64: ("AUTO_SAVE", 0, "Auto save"),
    65: ("PLACE", 1, "Set place"),
    66: ("OPEN_NAME", 1, "Open character name"),
    67: ("NAME", 2, "Set character name text"),
    68: ("LOG_NEW", 1, "New log file"),
    69: ("LOG_OUT", -1, "Log output"),
    70: ("SET_PARAM", 3, "Set parameter"),
    71: ("GET_PARAM", 2, "Get parameter"),
    72: ("ACTMENU", 1, "Action menu"),
    73: ("BATTLE", 0, "Start battle"),
    74: ("RESULT", 0, "Show result"),
    75: ("SET_PLAYER", 2, "Set player"),
    76: ("SET_HEROIN", 3, "Set heroine"),
    77: ("INIT_DK", 4, "Init DK"),
    78: ("SET_NORMA", 2, "Set norma"),
    79: ("GET_NORMA", 0, "Get norma"),
    80: ("GET_MINIEV_RESULT", 0, "Get mini event result"),
    81: ("GET_CHAR_JEM", 1, "Get character jewelry"),
}

VOC_MASK = 65536


class ESCRScript:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.index_count: int = 0
        self.index: List[int] = []
        self.code_size: int = 0
        self.code: bytes = b""
        self.data_size: int = 0
        self.data: bytes = b""

        self._load(filepath)

    def _load(self, filepath: str):
        with open(filepath, "rb") as f:
            # Read magic header
            magic = f.read(8)
            if magic != MAGIC_ESCR:
                raise ValueError(f"Invalid magic header: expected {MAGIC_ESCR}, got {magic}")

            # Read INDEX section
            self.index_count = struct.unpack("<I", f.read(4))[0]
            self.index = list(struct.unpack(f"<{self.index_count}I", f.read(4 * self.index_count)))

            # Read CODE section
            self.code_size = struct.unpack("<I", f.read(4))[0]
            self.code = f.read(self.code_size)

            # Read DATA section
            self.data_size = struct.unpack("<I", f.read(4))[0]
            self.data = f.read(self.data_size)

    def get_string(self, index: int, encoding: str = "cp932", convert_fullwidth: bool = True) -> str:
        if index >= self.index_count:
            return f"<invalid_index:{index}>"

        offset = self.index[index]
        if offset >= self.data_size:
            return f"<invalid_offset:{offset}>"

        # Find null terminator
        end = self.data.find(b"\x00", offset)
        if end == -1:
            end = self.data_size

        try:
            text = self.data[offset:end].decode(encoding, errors="replace")

            if convert_fullwidth:
                # Use Unicode normalization to convert halfwidth to fullwidth
                # NFKC: Compatibility Decomposition, followed by Canonical Composition
                # This converts halfwidth katakana (0xFF61-0xFF9F) to fullwidth (0x30A0-0x30FF)
                text = unicodedata.normalize("NFKC", text)

            return text
        except Exception as e:
            return f"<decode_error:{e}>"


class ESCRDecompiler:
    def __init__(self, script: ESCRScript, encoding: str = "cp932"):
        self.script = script
        self.encoding = encoding
        self.pc = 0  # Program counter
        self.instructions: List[Tuple[int, str, List]] = []

    def decompile(self) -> List[Tuple[int, str, List]]:
        self.pc = 0
        self.instructions = []

        while self.pc < len(self.script.code):
            offset = self.pc
            opcode = self._read_byte()

            if opcode in OPCODES:
                name, _, desc = OPCODES[opcode]
                params = []

                # Handle opcodes with inline parameters
                if opcode == 1:  # JUMP
                    target = self._read_int32()
                    params.append(f"@{target:04X}")
                elif opcode == 2:  # JUMPZ
                    target = self._read_int32()
                    params.append(f"@{target:04X}")
                elif opcode == 3:  # CALL
                    target = self._read_int32()
                    params.append(f"@{target:04X}")
                elif opcode == 5:  # PUSH
                    value = self._read_int32()
                    params.append(str(value))
                elif opcode == 7:  # STR
                    index = self._read_int32()
                    string_val = self.script.get_string(index, self.encoding)
                    params.append(f'{index} ; "{string_val}"')
                elif opcode == 33:  # LINE
                    line_num = self._read_int32()
                    params.append(str(line_num))

                self.instructions.append((offset, name, params))

            elif opcode >= RESERVE_COUNT:
                # User-defined command (PROC)
                proc_id = opcode - RESERVE_COUNT

                # Look up PROC command info
                if proc_id in PROC_COMMANDS:
                    name, expected_params, desc = PROC_COMMANDS[proc_id]
                else:
                    name = f"PROC_{proc_id}"
                    desc = "Unknown PROC command"

                params = []
                if self.pc < len(self.script.code):
                    maybe_count = self._peek_int32()
                    if 0 <= maybe_count <= 32:  # Reasonable param count
                        param_count = self._read_int32()
                        params.append(f"argc={param_count}")

                        # Add description for known commands
                        if proc_id in PROC_COMMANDS:
                            params.append(f"; {desc}")
                    else:
                        if proc_id in PROC_COMMANDS:
                            params.append(f"; {desc}")

                self.instructions.append((offset, name, params))

            else:
                # Unknown opcode
                self.instructions.append((offset, f"UNK_{opcode}", []))

        return self.instructions

    def _read_byte(self) -> int:
        if self.pc >= len(self.script.code):
            raise IndexError("PC out of bounds")
        value = self.script.code[self.pc]
        self.pc += 1
        return value

    def _read_int32(self) -> int:
        if self.pc + 4 > len(self.script.code):
            raise IndexError("Not enough bytes for int32")
        value = struct.unpack("<i", self.script.code[self.pc : self.pc + 4])[0]
        self.pc += 4
        return value

    def _peek_int32(self) -> int:
        if self.pc + 4 > len(self.script.code):
            raise IndexError("Not enough bytes for int32")
        return struct.unpack("<i", self.script.code[self.pc : self.pc + 4])[0]

    def format_output(self, show_hex: bool = True) -> str:
        lines = []
        lines.append(f"File: {os.path.basename(self.script.filepath)}")
        lines.append(f"Index Count: {self.script.index_count}")
        lines.append(f"Code Size: {self.script.code_size}")
        lines.append(f"Data Size: {self.script.data_size}")
        lines.append("")
        lines.append("STRING TABLE:")
        for i in range(min(self.script.index_count, 100)):  # Limit output
            s = self.script.get_string(i, self.encoding)
            disp = s.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
            lines.append(f'  [{i}] "{disp}"')
        if self.script.index_count > 100:
            lines.append(f"  ... ({self.script.index_count - 100} more strings)")
        lines.append("")
        lines.append("CODE:")

        for offset, name, params in self.instructions:
            param_str = ", ".join(params) if params else ""
            if show_hex:
                lines.append(f"  {offset:06X}: {name:12} {param_str}")
            else:
                lines.append(f"  {offset:6d}: {name:12} {param_str}")

        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python escr1_decompiler.py <script.bin> [output.txt]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file + ".txt"

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    try:
        print(f"Loading script: {input_file}")
        script = ESCRScript(input_file)

        print("Decompiling...")
        decompiler = ESCRDecompiler(script, encoding="cp932")
        decompiler.decompile()

        print("Formatting output...")
        output = decompiler.format_output(show_hex=True)

        print(f"Writing to: {output_file}")
        with open(output_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(output)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
