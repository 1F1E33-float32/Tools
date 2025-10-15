def u8(value: int) -> int:
    return value & 0xFF


def s8(value: int) -> int:
    value = u8(value)
    return value if value < 0x80 else value - 0x100


def u16(value: int) -> int:
    return value & 0xFFFF


def s16(value: int) -> int:
    value = u16(value)
    return value if value < 0x8000 else value - 0x10000


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def s32(value: int) -> int:
    value = u32(value)
    return value if value < 0x80000000 else value - 0x100000000
