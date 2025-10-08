from enum import IntEnum
from typing import List, Optional

from .extensions import BinaryReaderHelper


class ExprEvalResult(IntEnum):
    INTEGER = 0
    STRING = 1
    DECIMAL = 2
    RAW = 3


class ResultValidateMode(IntEnum):
    VALIDATE_MINIMUM = 0
    UNKNOWN_1 = 1
    UNKNOWN_2 = 2
    UNKNOWN_3 = 3
    UNKNOWN_4 = 4
    UNKNOWN_5 = 5
    UNKNOWN_6 = 6
    UNKNOWN_7 = 7
    UNKNOWN_8 = 8
    UNKNOWN_9 = 9
    UNKNOWN_10 = 10
    UNKNOWN_11 = 11
    UNKNOWN_12 = 12
    UNKNOWN_13 = 13
    UNKNOWN_14 = 14
    UNKNOWN_15 = 15


class ExpressionInfo:
    def __init__(self):
        self.keyword: str = ""
        self.result_type: ExprEvalResult = ExprEvalResult.INTEGER
        self.validate_mode: ResultValidateMode = ResultValidateMode.VALIDATE_MINIMUM

    def __str__(self) -> str:
        return f"Arg({self.keyword}), Type:({self.result_type.name})"


class CommandInfo:
    def __init__(self):
        self.name: str = ""
        self.arg_exprs: List[ExpressionInfo] = []

    def __str__(self) -> str:
        return f"Cmd({self.name}), ArgExprs:({len(self.arg_exprs)})"


class YSCM:
    MAGIC = 0x4D435359  # 'YSCM'

    def __init__(self):
        self._commands_info: List[CommandInfo] = []
        self._error_message: List[str] = []
        self._unknown_block: bytes = b""

    @property
    def commands_info(self) -> List[CommandInfo]:
        return self._commands_info

    def get_expr_info(self, command_id: int, expr_id: int) -> Optional[ExpressionInfo]:
        if command_id >= len(self._commands_info):
            return None

        cmd = self._commands_info[command_id]
        if expr_id >= len(cmd.arg_exprs):
            return None

        return cmd.arg_exprs[expr_id]

    def load(self, file_path: str):
        with open(file_path, "rb") as f:
            self._read(BinaryReaderHelper(f))

    def _read(self, reader: BinaryReaderHelper):
        # Read and validate magic number
        magic = reader.read_int32()
        if magic != self.MAGIC:
            raise ValueError("Not a valid YSCM file.")

        # Read version (unused)
        _ = reader.read_int32()

        # Read command count
        count = reader.read_int32()

        # Read zero padding
        reader.read_int32()

        # Read commands
        self._commands_info = []
        for i in range(count):
            cmd = CommandInfo()

            # Read command name
            cmd.name = reader.read_ansi_string()

            # Read action count
            action_count = reader.read_byte()

            # Read expressions
            cmd.arg_exprs = []
            for j in range(action_count):
                expr = ExpressionInfo()
                expr.keyword = reader.read_ansi_string()
                expr.result_type = ExprEvalResult(reader.read_byte())
                # Read validate mode as raw byte (may have unknown values)
                validate_byte = reader.read_byte()
                try:
                    expr.validate_mode = ResultValidateMode(validate_byte)
                except ValueError:
                    # Use raw byte value if not in enum
                    expr.validate_mode = validate_byte
                cmd.arg_exprs.append(expr)

            self._commands_info.append(cmd)

        # Read error messages
        self._error_message = []
        for i in range(37):
            msg = reader.read_ansi_string()
            self._error_message.append(msg)

        # Read unknown block
        self._unknown_block = reader.read_bytes(256)
