import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
info = logging.info
error = logging.error


class Saveloader:
    @classmethod
    def new(cls) -> "Saveloader":
        return cls()

    def load_raw(self, path: str) -> bytes:
        p = Path(path)
        if not p.exists():
            raise IOError(f"File not found: {path}")
        return p.read_bytes()

    def save_from(self, path: str, data) -> None:
        p = Path(path)
        if isinstance(data, (bytes, bytearray)):
            p.write_bytes(bytes(data))
        elif isinstance(data, str):
            p.write_text(data, encoding="utf-8")
        elif isinstance(data, list):
            # Rust 里是 Vec<String>，这里按行写出
            p.write_text("\n".join(map(str, data)) + "\n", encoding="utf-8")
        else:
            # 兜底：转成字符串
            p.write_text(str(data), encoding="utf-8")


class Engine:
    def unscramble(self) -> None:  # 与 Rust trait 同名
        raise NotImplementedError


VALID_SIGNATURES: List[bytes] = [
    b"BSXScript 3.0\x00\x00\x00",
    b"BSXScript 3.1\x00\x00\x00",
    b"BSXScript 3.2\x00\x00\x00",
    b"BSXScript 3.3\x00\x00\x00",
]


@dataclass
class BSXDecoder:
    script_buffer: bytes
    code_block_size: int
    code_block_offset: int
    name_offsets: List[int]
    message_offsets: List[int]

    def __init__(self, script_buffer: bytes):
        self.script_buffer = script_buffer

        header = script_buffer[:16]
        if header in VALID_SIGNATURES:
            info(f"Header: {header!r} verified!")
        else:
            error(f"No valid header found, instead found {header!r}")

        # *********************** CODE BLOCK ************************
        self.code_block_offset = self.read_four_le_bytes_from(script_buffer, 0x2C)
        self.code_block_size = self.read_four_le_bytes_from(script_buffer, 0x30)
        info("Code block headers extracted!")

        # *********************** NAME BLOCK ************************
        name_offset_list_offset = self.read_four_le_bytes_from(script_buffer, 0x88)
        name_offset_list_size = self.read_four_le_bytes_from(script_buffer, 0x8C) >> 2
        name_block_start = self.read_four_le_bytes_from(script_buffer, 0x90)
        info("Name block headers extracted!")

        # ********************* MESSAGE BLOCK ***********************
        message_offset_list_offset = self.read_four_le_bytes_from(script_buffer, 0x98)
        message_offset_list_size = self.read_four_le_bytes_from(script_buffer, 0x9C) >> 2
        message_block_start = self.read_four_le_bytes_from(script_buffer, 0xA0)
        info("Message block headers extracted!")

        # ---------------------- NAME OFFSETS -----------------------
        name_offsets: List[int] = []
        for i in range(name_offset_list_size):
            # 读取偏移表中的第 i 项（u32，小端）
            off = self.read_four_le_bytes_from(script_buffer, name_offset_list_offset + i * 4)
            # 偏移以 UTF-16 码元计数，因此 *2 转字节，并以 name_block_start 为基准
            name_offsets.append(name_block_start + off * 2)
        info("Name offsets extracted!")

        # --------------------- MESSAGE OFFSETS ---------------------
        message_offsets: List[int] = []
        for i in range(message_offset_list_size):
            off = self.read_four_le_bytes_from(script_buffer, message_offset_list_offset + i * 4)
            message_offsets.append(message_block_start + off * 2)
        info("Message offsets extracted!")

        self.name_offsets = name_offsets
        self.message_offsets = message_offsets

    # ---------------------- 公有方法 ----------------------

    def unscramble_text(self) -> List[str]:
        info("Unscrambling started.")
        code_start = int(self.code_block_offset)
        code_end = code_start + int(self.code_block_size)
        code = self.script_buffer[code_start:code_end]

        lines: List[str] = []
        current_address = 0
        current_speaker = "DEFAULT_NAME"

        while current_address < len(code):
            opcode = code[current_address]

            # 与 Rust 的 match 分支等价
            if (0x00 <= opcode <= 0x02) or opcode in (0x0A, 0x0B) or (0x1E <= opcode <= 0x32) or opcode in (0x35, 0x37, 0x39) or (0x3F <= opcode <= 0x41):
                current_address += 1

            elif (0x03 <= opcode <= 0x06) or opcode in (0x07, 0x08, 0x09, 0x34, 0x36, 0x38):
                current_address += 5

            elif (0x0C <= opcode <= 0x11) or (0x13 <= opcode <= 0x19) or (0x3A <= opcode <= 0x3C) or opcode == 0x12:
                current_address += 18

            elif (0x1A <= opcode <= 0x1C) or opcode == 0x3D:
                current_address += 12

            elif opcode == 0x33:
                current_address += 13

            elif opcode == 0x3E:
                # count 紧随其后 (LE u32)
                if current_address + 5 > len(code):
                    break
                count = self.read_four_le_bytes_from(code, current_address + 1)
                current_address += int(5 + 4 * count)

            elif opcode == 0x1D:
                if current_address + 2 > len(code):
                    break

                message_type = code[current_address + 1]
                message_id: Optional[int] = None
                name_id: Optional[int] = None

                if message_type == 0:
                    message_id = self.read_four_le_bytes_from(code, current_address + 2)
                elif message_type in (1, 2, 3):
                    message_id = self.read_four_le_bytes_from(code, current_address + 2)
                    name_id = self.read_four_le_bytes_from(code, current_address + 6)
                else:
                    error(f"Unknown message type discovered at 0x{current_address:X}! Type: {message_type}")
                    break

                if name_id is not None and name_id < len(self.name_offsets):
                    s = self.get_string_at(int(self.name_offsets[name_id]))
                    if s is not None:
                        info(f"Name found: {s}")
                        current_speaker = s

                if message_id is not None and message_id < len(self.message_offsets):
                    m = self.get_string_at(int(self.message_offsets[message_id]))
                    if m is not None:
                        self.add_line_to(lines, current_speaker, message_id, m)

                v2 = code[current_address + 1]
                v1 = 0
                if v2 > 1 and (current_address + 14) < len(code):
                    v1 = 4 * self.read_four_le_bytes_from(code, current_address + 10)

                current_address += int(v1 + 4 * v2 + 6)

            else:
                error(f"Unknown opcode at 0x{current_address:X}!")
                break

        return lines

    def collect_names(self) -> List[str]:
        """
        等价于 Rust 的 collect_names() -> Vec<String>
        以 "[{id:07X}][{name}]" 形式返回
        """
        names: List[str] = []
        for idx, off in enumerate(self.name_offsets):
            s = self.get_string_at(int(off))
            if s is not None:
                names.append(f"[{idx:07X}][{s}]")
        return names

    @staticmethod
    def read_four_le_bytes_from(buf: bytes, offset: int) -> int:
        """
        等价于 Rust 的 read_four_le_bytes_from()
        失败时抛出 IOError，以匹配 Rust 中的 io::Error 行为。
        """
        if offset < 0 or offset + 4 > len(buf):
            raise IOError(f"Out of bounds at offset {offset}!")
        try:
            b0, b1, b2, b3 = buf[offset : offset + 4]
        except Exception:
            raise IOError(f"Couldn't convert 4 bytes at offset {offset} into array!")
        return int.from_bytes(bytes((b0, b1, b2, b3)), byteorder="little", signed=False)

    def get_string_at(self, offset: int) -> Optional[str]:
        """
        等价于 Rust 的 get_string_at()
        从给定偏移起读取以双零结束的 UTF-16LE 字符串。
        """
        pos = offset
        end = pos
        b = self.script_buffer
        # 找到 0x00 0x00 终止（不包含终止符）
        while end + 1 < len(b):
            if b[end] == 0 and b[end + 1] == 0:
                break
            end += 2
        # 边界保护：如果越界或长度为奇数，尝试截断到偶数
        end = min(end, len(b))
        if (end - pos) < 0:
            return None
        length = end - pos
        if length < 2:
            return ""
        if length % 2 != 0:
            length -= 1
        try:
            return b[pos : pos + length].decode("utf-16le", errors="strict")
        except Exception:
            # 与 Rust 的 .ok() 语义一致：失败返回 None
            return None

    @staticmethod
    def add_line_to(lines: List[str], speaker: str, index: int, text: str) -> None:
        """
        等价于 Rust 的 add_line_to()
        追加格式化的台词行，并记录 info 日志。
        """
        line = f"[{index:07X}][{speaker}]: {text}"
        lines.append(line)
        info(f"[{speaker}]: {text}")


class BishopEngine(Engine):
    def __init__(self) -> None:
        saveloader = Saveloader.new()
        # 与 Rust: saveloader.load_raw("bsxx.dat") 保持一致
        bytes_buf = saveloader.load_raw(r"E:\VN_TMP\2025_09\隷従の制服\bsxx.dat")
        unscrambler = BSXDecoder(bytes_buf)
        self.unscrambler = unscrambler
        self.saveloader = saveloader

    def unscramble(self) -> None:
        result_data = self.unscrambler.unscramble_text()
        self.saveloader.save_from("bsxx.txt", result_data)
        name_data = self.unscrambler.collect_names()
        self.saveloader.save_from("name_list.txt", name_data)


if __name__ == "__main__":
    try:
        engine = BishopEngine()
        engine.unscramble()
        info("Done.")
    except Exception as e:
        error(str(e))
        raise
