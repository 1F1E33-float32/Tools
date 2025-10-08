from dataclasses import dataclass
from typing import List

from .extensions import BinaryReaderHelper


@dataclass
class YSKeywordDefine:
    name: str
    a: int
    b: int
    c: int
    d: int

    def __str__(self) -> str:
        return self.name


@dataclass
class YSCommandDefine:
    name: str
    keyword_count: int
    keywords: List[YSKeywordDefine]

    def __str__(self) -> str:
        kw_str = ", ".join(str(kw) for kw in self.keywords)
        return f"{self.name}[{kw_str}]"


@dataclass
class YSReservedVariableDefine:
    name: str
    type: int  # YSVR.VariableType
    dimensions: List[int]


class YSCD:
    MAGIC = 0x44435359  # 'YSCD'

    # Static class variables
    _commands: List[YSCommandDefine] = []
    _vars: List[YSReservedVariableDefine] = []

    @staticmethod
    def get_reserved_vars() -> List[YSReservedVariableDefine]:
        return YSCD._vars

    @staticmethod
    def load(file_path: str):
        with open(file_path, "rb") as f:
            YSCD._read(BinaryReaderHelper(f))

    @staticmethod
    def _read(reader: BinaryReaderHelper):
        # Read and validate magic number
        magic = reader.read_int32()
        if magic != YSCD.MAGIC:
            raise ValueError("Not a valid YSCD file.")

        # Read version (unused)
        _ = reader.read_int32()

        # Read command count
        cmd_count = reader.read_int32()

        # Read zero padding
        reader.read_int32()

        # Read commands
        YSCD._commands = []
        for i in range(cmd_count):
            name = reader.read_ansi_string()
            kw_count = reader.read_byte()

            keywords = []
            for j in range(kw_count):
                kw_name = reader.read_ansi_string()
                a = reader.read_byte()
                b = reader.read_byte()
                c = reader.read_byte()
                d = reader.read_byte()

                keywords.append(YSKeywordDefine(kw_name, a, b, c, d))

            YSCD._commands.append(YSCommandDefine(name, kw_count, keywords))

        # Read variable count
        var_count = reader.read_int32()

        # Read zero padding
        reader.read_int32()

        # Read reserved variables
        YSCD._vars = []
        for i in range(var_count):
            name = reader.read_ansi_string()
            var_type = reader.read_byte()  # YSVR.VariableType
            dim_count = reader.read_byte()

            dimensions = []
            for j in range(dim_count):
                dimensions.append(reader.read_uint32())

            YSCD._vars.append(YSReservedVariableDefine(name, var_type, dimensions))
