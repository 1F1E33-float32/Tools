import struct
from typing import BinaryIO, Optional


class Extensions:
    _DEFAULT_ENCODING = "shift_jis"

    @staticmethod
    def get_default_encoding() -> str:
        return Extensions._DEFAULT_ENCODING

    @staticmethod
    def read_ansi_string(reader: BinaryIO, length: Optional[int] = None, encoding: Optional[str] = None) -> str:
        if encoding is None:
            encoding = Extensions._DEFAULT_ENCODING

        if length is not None:
            # Fixed-length read
            buffer = reader.read(length)
            return buffer.decode(encoding, errors="replace")
        else:
            # Null-terminated read
            buffer = bytearray()
            while True:
                b = reader.read(1)
                if not b or b[0] == 0:
                    break
                buffer.append(b[0])

            if len(buffer) == 0:
                return ""

            return buffer.decode(encoding, errors="replace")

    @staticmethod
    def transpose(source: list[list]) -> list[list]:
        if not source or len(source) == 0:
            return []

        column_count = max(len(row) for row in source)

        result = []
        for col in range(column_count):
            column = []
            for row in source:
                if col < len(row):
                    column.append(row[col])
                else:
                    column.append(None)
            result.append(column)

        return result


class CheckSum:
    _CRC32_TABLE = None

    @staticmethod
    def _init_crc32_table():
        if CheckSum._CRC32_TABLE is not None:
            return

        CheckSum._CRC32_TABLE = []
        for i in range(256):
            k = i
            for j in range(8):
                if k & 1:
                    k = (k >> 1) ^ 0xEDB88320
                else:
                    k >>= 1
            CheckSum._CRC32_TABLE.append(k)

    @staticmethod
    def crc32(data: bytes) -> int:
        CheckSum._init_crc32_table()

        crc = 0xFFFFFFFF
        for byte in data:
            crc = (crc >> 8) ^ CheckSum._CRC32_TABLE[(crc & 0xFF) ^ byte]

        return (~crc) & 0xFFFFFFFF

    @staticmethod
    def adler32(data: bytes) -> int:
        MOD = 65521
        a = 1
        b = 0

        for byte in data:
            a = (a + byte) % MOD
            b = (b + a) % MOD

        return ((b << 16) | a) & 0xFFFFFFFF

    @staticmethod
    def murmur_hash2(data: bytes, seed: int = 0) -> int:
        m = 0x5BD1E995
        r = 24

        length = len(data)
        h = seed ^ length

        index = 0
        while length >= 4:
            k = struct.unpack("<I", data[index : index + 4])[0]

            k = (k * m) & 0xFFFFFFFF
            k ^= k >> r
            k = (k * m) & 0xFFFFFFFF

            h = (h * m) & 0xFFFFFFFF
            h ^= k

            index += 4
            length -= 4

        # Handle remaining bytes
        if length > 0:
            if length > 2:
                h ^= data[index + 2] << 16
            if length > 1:
                h ^= data[index + 1] << 8
            h ^= data[index]
            h = (h * m) & 0xFFFFFFFF

        h ^= h >> 13
        h = (h * m) & 0xFFFFFFFF
        h ^= h >> 15

        return h & 0xFFFFFFFF


class BinaryReaderHelper:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def read_byte(self) -> int:
        return struct.unpack("B", self.stream.read(1))[0]

    def read_sbyte(self) -> int:
        return struct.unpack("b", self.stream.read(1))[0]

    def read_uint16(self) -> int:
        return struct.unpack("<H", self.stream.read(2))[0]

    def read_int16(self) -> int:
        return struct.unpack("<h", self.stream.read(2))[0]

    def read_uint32(self) -> int:
        return struct.unpack("<I", self.stream.read(4))[0]

    def read_int32(self) -> int:
        return struct.unpack("<i", self.stream.read(4))[0]

    def read_int64(self) -> int:
        return struct.unpack("<q", self.stream.read(8))[0]

    def read_double(self) -> float:
        return struct.unpack("<d", self.stream.read(8))[0]

    def read_bytes(self, count: int) -> bytes:
        return self.stream.read(count)

    def read_ansi_string(self, length: Optional[int] = None, encoding: Optional[str] = None) -> str:
        return Extensions.read_ansi_string(self.stream, length, encoding)

    @property
    def position(self) -> int:
        return self.stream.tell()

    @position.setter
    def position(self, value: int):
        self.stream.seek(value)

    def seek(self, offset: int, whence: int = 0):
        self.stream.seek(offset, whence)
