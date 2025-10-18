from __future__ import annotations

import struct


def u8(data: bytes, off: int) -> int:
    return data[off]


def u16(data: bytes, off: int, be: bool) -> int:
    return struct.unpack_from(">H" if be else "<H", data, off)[0]


def u32(data: bytes, off: int, be: bool) -> int:
    return struct.unpack_from(">I" if be else "<I", data, off)[0]


def read_fourcc(data: bytes, off: int) -> bytes:
    return data[off: off + 4]


def le16(n: int) -> bytes:
    return struct.pack("<H", n & 0xFFFF)


def le16s(n: int) -> bytes:
    return struct.pack("<h", n)


def le32(n: int) -> bytes:
    return struct.pack("<I", n & 0xFFFFFFFF)