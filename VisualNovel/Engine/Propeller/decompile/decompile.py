import argparse
import struct
from pathlib import Path
from typing import List, Tuple, Union


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, default=Path(r"E:\VN\_tmp\#JA\星降る夜のファルネーゼ"))
    parser.add_argument("--encoding", default=r"cp932")
    return parser.parse_args()


COMMAND_LIBRARY = [
    [  # mode 0
        ["00 00", "BIh", "INIT"],
        ["00 01", "BBhHBhH", "JUMP_1"],
        ["00 02", "Bh", "JUMP_2"],
        ["00 03", "Bh", ""],
        ["00 04", "", "RETURN"],
        ["00 05", "BhB", "PAUSE"],
        ["00 06", "", "END"],
        ["00 07", "B", ""],
        ["00 08", "S", "GO_TO_SCRIPT"],
        ["00 09", "", ""],
        ["00 0a", "B", ""],
        ["00 0b", "", ""],
        ["00 0c", "", ""],
        ["00 0d", "", ""],
        ["00 0e", "", ""],
        ["00 0f", "", ""],
        ["00 10", "Bh", ""],
        ["00 11", "Bh", ""],
        ["00 12", "", ""],
        ["00 13", "", ""],
        ["00 14", "", ""],
        ["00 16", "B", ""],
        ["00 17", "Bh", ""],
        ["00 20", "BhBhH", ""],
        ["00 30", "", ""],
        ["00 31", "", ""],
        ["00 32", "", "CONFIRM_SCENARIO_NAME"],
        ["00 33", "Bh", "JUMP_3"],
        ["00 34", "Bh", ""],
        ["00 35", "", ""],
        ["00 36", "B", ""],
        ["00 37", "HiBh", ""],
        ["01 00", "S", "SET_GAME_TITLE"],
        ["01 01", "BS", "CALL_SCRIPT"],
        ["01 02", "Bh", ""],
        ["01 03", "SSS", ""],  # ISS
        ["01 04", "BS", ""],
        ["01 05", "BhBh", ""],
        ["01 06", "BhBh", ""],
        ["01 07", "BhBh", ""],
        ["01 08", "BhBhBhBhBhBhBh", ""],
        ["01 09", "SSSB", ""],
        ["01 0a", "BhBh", ""],  # BhBhBh #BhBh
        ["01 0b", "BhBhS", ""],
        ["01 0c", "HH", ""],
        ["01 0d", "BHSS", "SET_SCENARIO_NAME"],
        ["01 0e", "HhBhBhBh", ""],
        ["01 0f", "Bh", ""],
        ["01 10", "HhBhBh", ""],
        ["01 11", "Bh", ""],
        ["01 12", "BhBhBhBhBhBhBh", ""],
        ["01 13", "BhBhBhBhBh", ""],
        ["01 14", "Bh", ""],
        ["01 15", "BS", ""],
        ["01 16", "Bh", ""],
        ["01 17", "SS", ""],
        ["01 18", "S", ""],
        ["01 19", "SBh", ""],
        ["01 1a", "H", ""],
        ["01 1b", "Hh", ""],
        ["01 1c", "HhBh", ""],
        ["01 1d", "HhBh", ""],
        ["01 1e", "SS", ""],
        ["01 1f", "SSS", ""],
        ["02 00", "BhS", "SET_BG"],
        ["02 01", "BhBhBh", ""],
        ["02 02", "BhB", ""],
        ["02 03", "BhBhBhBhBh", ""],
        ["02 04", "BhBh", ""],
        ["02 05", "BhBhBh", ""],
        ["02 06", "BhBh", ""],
        ["02 07", "BhBh", ""],
        ["02 08", "BhBhBhBh", "SCREEN_MOTION"],
        ["02 09", "BhBhBhBhBhBh", ""],
        ["02 0a", "BhBhBh", ""],
        ["02 0b", "BhBhBhBh", ""],
        ["02 0c", "BhBhBhBhB", ""],
        ["02 0d", "BhBh", ""],
        ["02 0e", "BhBh", ""],
        ["02 0f", "BhBh", ""],
        ["02 10", "BhBhBh", ""],
        ["02 11", "BhBhBh", ""],
        ["02 12", "BhBhBhBhBhS", "SET_CHOICE_OPTION"],
        ["02 13", "BhBh", ""],
        ["02 14", "BhSBhBhBhB", ""],
        ["02 15", "BhBhBhBh", ""],
        ["02 16", "BhSBhBhBhBh", ""],
        ["02 17", "BhB", ""],
        ["03 00", "BhSBhB", "FADE_SCREEN"],
        ["03 01", "BhBhB", ""],
        ["03 02", "Bh", ""],
        ["03 03", "SB", ""],
        ["04 00", "BhHh", ""],
        ["04 01", "BhB", ""],
        ["04 02", "BhB", ""],
        ["04 03", "BhBh", ""],
        ["04 04", "BhBh", ""],
        ["05 00", "BhS", "MESSAGE"],
        ["05 01", "BhBhBhBhBhBhBhBh", ""],
        ["05 02", "BhBhBhBhBhBhBh", ""],
        ["05 03", "BhBh", ""],
        ["05 04", "BhBh", ""],
        ["05 05", "B", ""],
        ["05 06", "", ""],
        ["05 07", "H", ""],
        ["06 00", "SHh", "SET_BGM"],
        ["06 01", "Bh", ""],
        ["06 02", "S", "PLAY_VIDEO"],
        ["06 03", "", ""],
        ["06 04", "BhS", "PLAY_SE"],
        ["06 05", "BhB", ""],
        ["06 06", "Bh", ""],
        ["06 07", "", ""],
        ["06 08", "Bh", ""],
        ["06 09", "Bh", ""],
        ["06 0a", "S", ""],
        ["06 0b", "HiBh", ""],
        ["06 0c", "BhBhBhBh", ""],
        ["06 0d", "", ""],
        ["06 0e", "BhBh", ""],
    ],
    [  # mode 1
        ["00 00", "BIBBi", "INIT"],
        ["00 01", "BBiHBiI", "JUMP_1"],
        ["00 02", "Bi", "JUMP_2"],
        ["00 03", "Bi", ""],
        ["00 04", "", "RETURN"],
        ["00 05", "BiB", "PAUSE"],
        ["00 06", "", "END"],
        ["00 07", "B", ""],
        ["00 08", "S", "GO_TO_SCRIPT"],
        ["00 09", "", ""],
        ["00 0a", "B", ""],
        ["00 0b", "", ""],
        ["00 0c", "", ""],
        ["00 0d", "", ""],
        ["00 0e", "", ""],
        ["00 0f", "", ""],
        ["00 10", "Bi", ""],
        ["00 11", "Bi", ""],
        ["00 12", "", ""],
        ["00 13", "", ""],
        ["00 14", "", ""],
        ["00 16", "B", ""],
        ["00 17", "Bi", ""],
        ["00 20", "BiBiH", ""],
        ["00 30", "", ""],
        ["00 31", "", ""],
        ["00 32", "", "CONFIRM_SCENARIO_NAME"],
        ["00 33", "Bi", "JUMP_3"],
        ["00 34", "Bi", ""],
        ["00 35", "", ""],
        ["00 36", "B", ""],
        ["00 37", "HiBi", ""],
        ["01 00", "S", "SET_GAME_TITLE"],
        ["01 01", "BS", "CALL_SCRIPT"],  # BiS
        ["01 02", "Bi", ""],
        ["01 03", "ISS", ""],
        ["01 04", "BS", ""],
        ["01 05", "BiBi", ""],
        ["01 06", "BiBi", ""],
        ["01 07", "BiBi", ""],
        ["01 08", "BiBiBiBiBiBiBi", ""],
        ["01 09", "SSSB", ""],
        ["01 0a", "BiBi", ""],
        ["01 0b", "BiBiS", ""],
        ["01 0c", "HI", ""],
        ["01 0d", "BiSS", "SET_SCENARIO_NAME"],
        ["01 0e", "HiBiBiBi", ""],
        ["01 0f", "Bi", ""],
        ["01 10", "HiBiBi", ""],
        ["01 11", "Bi", ""],
        ["01 12", "BiBiBiBiBiBiBi", ""],
        ["01 13", "BiBiBiBiBi", ""],
        ["01 14", "Bi", ""],
        ["01 15", "BS", ""],
        ["01 16", "Bi", ""],
        ["01 17", "SS", ""],
        ["01 18", "S", ""],
        ["01 19", "SBi", ""],
        ["01 1a", "H", ""],
        ["01 1b", "Hi", ""],
        ["01 1c", "HiBi", ""],
        ["01 1d", "HiBi", ""],
        ["01 1e", "SS", ""],
        ["01 1f", "SSS", ""],
        ["02 00", "BiS", "SET_BG"],
        ["02 01", "BiBiBi", ""],
        ["02 02", "BiB", ""],
        ["02 03", "BiBiBiBiBi", ""],
        ["02 04", "BiBi", ""],
        ["02 05", "BiBiBi", ""],
        ["02 06", "BiBi", ""],
        ["02 07", "BiBi", ""],
        ["02 08", "BiBiBiBi", ""],
        ["02 09", "BiBiBiBiBiBi", ""],
        ["02 0a", "BiBiBi", ""],
        ["02 0b", "BiBiBiBi", ""],
        ["02 0c", "BiBiBiBiB", ""],
        ["02 0d", "BiBi", ""],
        ["02 0e", "BiBi", ""],
        ["02 0f", "BiBi", ""],
        ["02 10", "BiBiBi", ""],
        ["02 11", "BiBiBi", ""],
        ["02 12", "BiBiBiBiBiS", "SET_CHOICE_OPTION"],
        ["02 13", "BiBi", ""],
        ["02 14", "BiSBiBiBiB", ""],
        ["02 15", "BiBiBiBi", ""],
        ["02 16", "BiSBiBiBiBi", ""],
        ["02 17", "BiB", ""],
        ["03 00", "BiSBiB", "FADE_SCREEN"],
        ["03 01", "BiBiB", ""],
        ["03 02", "Bi", ""],
        ["03 03", "SB", ""],
        ["04 00", "BiHi", ""],
        ["04 01", "BiB", ""],
        ["04 02", "BiB", ""],
        ["04 03", "BiBi", ""],
        ["04 04", "BiBi", ""],
        ["05 00", "BIS", "MESSAGE"],
        ["05 01", "BiBiBiBiBiBiBiBi", ""],
        ["05 02", "BiBiBiBiBiBiBi", ""],
        ["05 03", "BiBi", ""],
        ["05 04", "BiBi", ""],
        ["05 05", "B", ""],
        ["05 06", "", ""],
        ["05 07", "H", ""],
        ["06 00", "SHi", "SET_BGM"],
        ["06 01", "Bi", ""],
        ["06 02", "S", "PLAY_VIDEO"],
        ["06 03", "", ""],
        ["06 04", "BiS", "PLAY_SE"],
        ["06 05", "BiB", ""],
        ["06 06", "Bi", ""],
        ["06 07", "", ""],
        ["06 08", "Bi", ""],
        ["06 09", "Bi", ""],
        ["06 0a", "S", ""],
        ["06 0b", "HiBi", ""],
        ["06 0c", "BiBiBiBi", ""],
        ["06 0d", "", ""],
        ["06 0e", "BiBi", ""],
        ["06 0f", "Bi", ""],  # Only latest game?
        ["06 11", "Bi", ""],  # Only latest game?
        ["06 13", "BiBi", ""],  # Only latest game?
        ["06 14", "BiBiBi", ""],  # Only latest game?
        ["06 15", "Bi", ""],  # Only latest game?
    ],
]


def decrypt_xor(data: bytes, key: int) -> bytes:
    return bytes([b ^ key for b in data])


class MscScript:
    def __init__(self, msc_path: Union[str, Path], txt_path: Union[str, Path], mode: int, encoding: str):
        self.msc_path = Path(msc_path)
        self.txt_path = Path(txt_path)
        self.encoding = encoding
        self.segments: List[int] = []
        self.params_one: List[List[int]] = []
        self.params_two: List[List[int]] = []
        self.pointer = 0
        self.commands: List[str] = []
        self.args: List[List[Union[int, str, bytes]]] = []
        self.offsets: List[Tuple[int, int]] = []
        self.mode = mode

        with open(self.msc_path, "rb") as f:
            file_data = f.read()
            # mode 0 不需要解密，否则用第一个字节作为密钥 xor
            if mode == 0:
                self.file_data = file_data
            else:
                key = file_data[0]
                self.file_data = decrypt_xor(file_data, key)
            self.file_len = len(self.file_data)

    def disassemble(self) -> None:
        self.reset_state()
        self.diss_header()
        self.diss_commands()

    def analyze_script(self) -> int:
        first = self.file_data[0]
        second = self.file_data[1]
        if first != second:
            raise Exception("This is not a valid .msc script!")
        if first == 0x00:
            return 0x00
        return 0x01

    def reset_state(self) -> None:
        self.pointer = 0
        self.segments = []
        self.params_one = []
        self.params_two = []
        self.commands = []
        self.args = []
        self.offsets = []

    def diss_header(self) -> None:
        assert self.file_data[0:2] == b"\x00\x00", "This is not a .msc script!"
        with open(r"1.bin", "wb") as f:
            f.write(self.file_data)
        self.pointer = 2

        self.segments.append(struct.unpack("I", self.file_data[2:6])[0])
        self.pointer = 6

        section_struct = "II"
        section_len = 9
        if self.mode == 0:
            section_struct = "HI"
            section_len = 7

        for i in range(1, 3):
            self.segments.append(struct.unpack("I", self.file_data[self.pointer : self.pointer + 4])[0])
            self.pointer += 4
            section_items = []
            for j in range(self.segments[i] // section_len):
                self.pointer += 1
                section_items.append([])
                for fmt in section_struct:
                    if fmt.upper() == "H":
                        section_items[j].append(struct.unpack(fmt, self.file_data[self.pointer : self.pointer + 2])[0])
                        self.pointer += 2
                    elif fmt.upper() == "I":
                        section_items[j].append(struct.unpack(fmt, self.file_data[self.pointer : self.pointer + 4])[0])
                        self.pointer += 4
                    else:
                        raise Exception("Unsupported struct format!")
            if i == 1:
                self.params_one += section_items
            elif i == 2:
                self.params_two += section_items

    def diss_commands(self) -> None:
        with open(self.txt_path, "w", encoding=self.encoding) as out_f:
            free_bytes = False
            free_bytes_buf = b""
            out_f.write("#VERSION " + str(self.mode) + "\n")
            out_f.write("#ENCODING " + str(self.encoding) + "\n")

            while self.pointer < self.file_len:
                for p in self.params_one:
                    if (self.pointer - self.segments[0]) == p[1]:
                        out_f.write("#2-" + str(p[0]) + "\n")
                for p in self.params_two:
                    if (self.pointer - self.segments[0]) == p[1]:
                        out_f.write("#3-" + str(p[0]) + "\n")
                for o in self.offsets:
                    if (self.pointer - self.segments[0]) == o[1]:
                        out_f.write("#4-" + str(o[0]) + "\n")

                cmd_bytes = self.file_data[self.pointer : self.pointer + 2]
                self.pointer += 2
                cmd_index = -1
                for i, entry in enumerate(COMMAND_LIBRARY[self.mode]):
                    if cmd_bytes.hex(" ") == entry[0]:
                        cmd_index = i
                        break

                if cmd_index == -1:
                    if not free_bytes:
                        out_f.write("#0-")
                        free_bytes = True
                    free_bytes_buf += cmd_bytes
                    continue

                if free_bytes:
                    out_f.write(free_bytes_buf.hex(" "))
                    out_f.write("\n")
                    free_bytes = False
                    free_bytes_buf = b""

                out_f.write("#1-")
                name = COMMAND_LIBRARY[self.mode][cmd_index][2]
                if name:
                    out_f.write(name)
                else:
                    out_f.write(cmd_bytes.hex(" "))
                out_f.write("\n")

                args_out = []
                fmt_str = COMMAND_LIBRARY[self.mode][cmd_index][1]
                for ch in fmt_str:
                    up = ch.upper()
                    if up == "B":
                        args_out.append(struct.unpack(ch, self.file_data[self.pointer : self.pointer + 1])[0])
                        self.pointer += 1
                    elif up == "H":
                        args_out.append(struct.unpack(ch, self.file_data[self.pointer : self.pointer + 2])[0])
                        self.pointer += 2
                    elif up == "I":
                        args_out.append(struct.unpack(ch, self.file_data[self.pointer : self.pointer + 4])[0])
                        self.pointer += 4
                    elif up == "S":
                        str_len_fmt = "I"
                        str_len_size = 4
                        if self.mode == 0:
                            str_len_fmt = "H"
                            str_len_size = 2
                        strlen = struct.unpack(str_len_fmt, self.file_data[self.pointer : self.pointer + str_len_size])[0]
                        self.pointer += str_len_size
                        sbytes = self.file_data[self.pointer : self.pointer + strlen]
                        try:
                            args_out.append(sbytes.decode(self.encoding))
                        except Exception:
                            args_out.append(sbytes)
                        self.pointer += strlen
                    else:
                        raise Exception(f"Unsupported arg type: {ch}")
                out_f.write(str(args_out))
                if self.pointer < self.file_len:
                    out_f.write("\n")

            if free_bytes:
                out_f.write(free_bytes_buf.hex(" "))


if __name__ == "__main__":
    args = args_parse()
    folder = args.folder.resolve()
    encoding = args.encoding

    msc_files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".msc"])

    for msc_path in msc_files:
        tmp = MscScript(msc_path, msc_path.with_suffix(msc_path.suffix + ".txt"), 0, encoding)
        mode = tmp.analyze_script()
        out_path = msc_path.with_suffix(msc_path.suffix + ".txt")
        script = MscScript(msc_path, out_path, mode, encoding)
        print(msc_path)
        script.disassemble()
