from enum import IntEnum, IntFlag


class MjoType(IntEnum):
    INT = 0
    FLOAT = 1
    STRING = 2
    INT_ARRAY = 3
    FLOAT_ARRAY = 4
    STRING_ARRAY = 5
    UNKNOWN = 255


class MjoTypeMask(IntFlag):
    INT = 1 << MjoType.INT
    FLOAT = 1 << MjoType.FLOAT
    STRING = 1 << MjoType.STRING
    INT_ARRAY = 1 << MjoType.INT_ARRAY
    FLOAT_ARRAY = 1 << MjoType.FLOAT_ARRAY
    STRING_ARRAY = 1 << MjoType.STRING_ARRAY

    NUMERIC = INT | FLOAT
    PRIMITIVE = INT | FLOAT | STRING
    ARRAY = INT_ARRAY | FLOAT_ARRAY | STRING_ARRAY
    ALL = PRIMITIVE | ARRAY
    NONE = 0


class MjoScope(IntEnum):
    PERSISTENT = 0
    SAVE_FILE = 1
    THREAD = 2
    LOCAL = 3


class MjoInvertMode(IntEnum):
    NONE = 0
    NUMERIC = 1
    BOOLEAN = 2
    BITWISE = 3


class MjoModifier(IntEnum):
    NONE = 0
    PRE_INCREMENT = 1
    PRE_DECREMENT = 2
    POST_INCREMENT = 3
    POST_DECREMENT = 4


class MjoFlagMask(IntFlag):
    DIM = 0b00011000_00000000
    TYPE = 0b00000111_00000000
    SCOPE = 0b00000000_11100000
    INVERT = 0b00000000_00011000
    MODIFIER = 0b00000000_00000111


class MjoFlags:
    @staticmethod
    def dimension(flags: int) -> int:
        return (flags & MjoFlagMask.DIM) >> 11

    @staticmethod
    def type(flags: int) -> MjoType:
        return MjoType((flags & MjoFlagMask.TYPE) >> 8)

    @staticmethod
    def scope(flags: int) -> MjoScope:
        return MjoScope((flags & MjoFlagMask.SCOPE) >> 5)

    @staticmethod
    def invert_mode(flags: int) -> MjoInvertMode:
        return MjoInvertMode((flags & MjoFlagMask.INVERT) >> 3)

    @staticmethod
    def modifier(flags: int) -> MjoModifier:
        return MjoModifier(flags & MjoFlagMask.MODIFIER)

    @staticmethod
    def build(type: MjoType, scope: MjoScope, modifier: MjoModifier, invert_mode: MjoInvertMode, dimension: int) -> int:
        return dimension << 11 | int(type) << 8 | int(scope) << 5 | int(invert_mode) << 3 | int(modifier)
