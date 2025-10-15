from typing import List


class Crc:
    @staticmethod
    def calculate_32(seed: int) -> int:
        POLY = 0xEDB88320
        value = seed & 0xFFFFFFFF
        for _ in range(8):
            if value & 1:
                value = (value >> 1) ^ POLY
            else:
                value = value >> 1
        return value & 0xFFFFFFFF

    @staticmethod
    def calculate_inverse_32(seed: int) -> int:
        msbyte = seed & 0xFF
        for i in range(256):
            if (Crc.calculate_32(i) >> 24) == msbyte:
                return i
        raise ValueError(f"Most significant byte 0x{msbyte:02x} not in CRC32 table")

    @staticmethod
    def crypt_32(data: bytearray, key_offset: int = 0) -> None:
        for i in range(len(data)):
            data[i] ^= _CRYPT_KEY_32[(key_offset + i) & 0x3FF]

    @staticmethod
    def hash_32(data: bytes, init: int = 0) -> int:
        result = (~init) & 0xFFFFFFFF

        for byte in data:
            result = ((result >> 8) ^ _CRC32_TABLE[(result ^ byte) & 0xFF]) & 0xFFFFFFFF

        return (~result) & 0xFFFFFFFF

    @staticmethod
    def hash_32_string(s: str, init: int = 0) -> int:
        data = s.encode("shift-jis")
        return Crc.hash_32(data, init)


# Build CRC32 tables on module load
_CRC32_TABLE: List[int] = [Crc.calculate_32(i) for i in range(256)]

# Build crypt key
_CRYPT_KEY_32 = bytearray()
for _value in _CRC32_TABLE:
    _CRYPT_KEY_32.extend(_value.to_bytes(4, "little"))
