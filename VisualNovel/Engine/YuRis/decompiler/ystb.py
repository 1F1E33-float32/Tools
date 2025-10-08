import io
import struct
from pathlib import Path
from typing import List, Optional

from .command_id_generator import CommandIDGenerator
from .expr_instruction_set import AssignExprInstSet, ExprInstructionSet
from .extensions import BinaryReaderHelper
from .instruction import (
    ArrayAccess,
    ByteLiteral,
    DecimalLiteral,
    IntLiteral,
    LongLiteral,
    ShortLiteral,
    VariableAccess,
    VariableRef,
)
from .yscm import YSCM, ExprEvalResult
from .yslb import YSLB


class CommandExpression:
    def __init__(self):
        self.id: int = 0
        self.flag: int = 0
        self.arg_load_fn: int = 0
        self.arg_load_op: int = 0
        self.instruction_size: int = 0
        self.instruction_offset: int = 0
        self.expr_insts: Optional[ExprInstructionSet] = None

    def get_load_op(self) -> str:
        ops = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "/=", 5: "%=", 6: "&=", 7: "|=", 8: "^="}
        return ops.get(self.arg_load_op, "")

    def __str__(self) -> str:
        return str(self.expr_insts) if self.expr_insts else ""


class Command:
    def __init__(self, cmd_id: int):
        self.offset: int = 0
        self.id: str = CommandIDGenerator.get_id(cmd_id)
        self.expr_count: int = 0
        self.label_id: int = 0
        self.line_number: int = 0
        self.expressions: List[CommandExpression] = []

    def __str__(self) -> str:
        cmd_name = self.id
        if not self.expressions or len(self.expressions) == 0:
            return f"{cmd_name}[]"

        args = []
        for expr in self.expressions:
            if expr.expr_insts is not None:
                args.append(str(expr.expr_insts))

        return f"{cmd_name}[{', '.join(args)}]"


class YSTB:
    MAGIC = 0x42545359  # 'YSTB'

    def __init__(self, yscm: YSCM, yslb: YSLB):
        self._script_id: int = -1
        self._script_buffer: bytes = b""

        self._command_addr: int = 0
        self._command_size: int = 0
        self._cmd_expr_addr: int = 0
        self._cmd_expr_size: int = 0
        self._cmd_data_addr: int = 0
        self._cmd_data_size: int = 0
        self._line_idx_addr: int = 0
        self._line_idx_size: int = 0

        self._commands: List[Command] = []

        self._yscm = yscm
        self._yslb = yslb

    @property
    def commands(self) -> List[Command]:
        return self._commands

    def _crypt(self, ybn_key: bytes):
        # Convert to bytearray for in-place modification
        buffer = bytearray(self._script_buffer)

        # Decrypt command section
        for i in range(self._command_size):
            buffer[self._command_addr + i] ^= ybn_key[i & 3]

        # Decrypt expression section
        for i in range(self._cmd_expr_size):
            buffer[self._cmd_expr_addr + i] ^= ybn_key[i & 3]

        # Decrypt data section
        for i in range(self._cmd_data_size):
            buffer[self._cmd_data_addr + i] ^= ybn_key[i & 3]

        # Decrypt line index section
        for i in range(self._line_idx_size):
            buffer[self._line_idx_addr + i] ^= ybn_key[i & 3]

        self._script_buffer = bytes(buffer)

    def load(self, file_path: str, script_id: int, ybn_key: Optional[bytes]) -> bool:
        if not Path(file_path).exists():
            return False

        self._script_id = script_id

        # Read entire file
        with open(file_path, "rb") as f:
            buffer = f.read()

        # Validate magic number
        magic = struct.unpack("<I", buffer[0:4])[0]
        if magic != self.MAGIC:
            raise ValueError("Not a valid YSTB file.")

        self._script_buffer = buffer

        # Parse header
        self._command_addr = 0x20
        self._command_size = struct.unpack("<I", self._script_buffer[0x0C:0x10])[0]

        self._cmd_expr_addr = self._command_addr + self._command_size
        self._cmd_expr_size = struct.unpack("<I", self._script_buffer[0x10:0x14])[0]

        self._cmd_data_addr = self._cmd_expr_addr + self._cmd_expr_size
        self._cmd_data_size = struct.unpack("<I", self._script_buffer[0x14:0x18])[0]

        self._line_idx_addr = self._cmd_data_addr + self._cmd_data_size
        self._line_idx_size = struct.unpack("<I", self._script_buffer[0x18:0x1C])[0]

        # Decrypt if key provided
        if ybn_key is not None:
            self._crypt(ybn_key)

        # Parse sections
        self._read_commands()
        self._read_command_line_numbers()
        self._read_command_expressions()
        self._read_command_expression_instructions()

        return True

    def _read_commands(self):
        stream = io.BytesIO(self._script_buffer)
        reader = BinaryReaderHelper(stream)

        reader.position = self._command_addr

        count = struct.unpack("<I", self._script_buffer[8:12])[0]

        self._commands = []
        for i in range(count):
            pos = reader.position
            cmd_id = reader.read_byte()
            cmd = Command(cmd_id)
            cmd.offset = pos
            cmd.expr_count = reader.read_byte()
            cmd.label_id = reader.read_uint16()

            self._commands.append(cmd)

        assert reader.position == self._command_addr + self._command_size

    def _read_command_expressions(self):
        stream = io.BytesIO(self._script_buffer)
        reader = BinaryReaderHelper(stream)

        reader.position = self._cmd_expr_addr

        for statement in self._commands:
            statement.expressions = []

            if statement.expr_count > 0:
                for i in range(statement.expr_count):
                    expr = CommandExpression()

                    expr.id = reader.read_byte()
                    expr.flag = reader.read_byte()
                    expr.arg_load_fn = reader.read_byte()
                    expr.arg_load_op = reader.read_byte()
                    expr.instruction_size = reader.read_int32()
                    expr.instruction_offset = reader.read_int32()

                    statement.expressions.append(expr)

        assert reader.position == self._cmd_expr_addr + self._cmd_expr_size

    def _read_command_line_numbers(self):
        stream = io.BytesIO(self._script_buffer)
        reader = BinaryReaderHelper(stream)

        reader.position = self._line_idx_addr

        for cmd in self._commands:
            cmd.line_number = reader.read_int32()

        assert reader.position == self._line_idx_addr + self._line_idx_size

    def _read_command_expression_instructions(self):
        # Get data span
        data_span = self._script_buffer[self._cmd_data_addr : self._cmd_data_addr + self._cmd_data_size]

        for i in range(len(self._commands)):
            if self._commands[i].expr_count == 0:
                continue

            o = 0
            while o < len(self._commands[i].expressions):
                expr = self._commands[i].expressions
                cmd_id_int = None

                # Get command ID as integer for YSCM lookup
                for idx, cmd_info in enumerate(self._yscm.commands_info):
                    if cmd_info.name == self._commands[i].id:
                        cmd_id_int = idx
                        break

                if cmd_id_int is None:
                    o += 1
                    continue

                info = self._yscm.get_expr_info(cmd_id_int, expr[o].id)

                string_expr = True
                cmd_name = self._commands[i].id.upper()

                # Preprocess special commands
                if cmd_name in ("IF", "ELSE"):
                    # Conditional expression
                    condition_expr = ExprInstructionSet(self._script_id)
                    inst_data = data_span[expr[o].instruction_offset : expr[o].instruction_offset + expr[o].instruction_size]
                    condition_expr.get_instructions(inst_data)
                    expr[o].expr_insts = condition_expr

                    # Remove branch destination expressions
                    if len(expr) > o + 2:
                        del expr[o + 1 : o + 3]
                    o += 1
                    continue

                elif cmd_name in ("S_INT", "S_STR", "S_FLT", "G_INT", "G_STR", "G_FLT", "F_INT", "F_STR", "F_FLT", "LET"):
                    # Assignment with destination and source
                    if o + 1 < len(expr):
                        dst = ExprInstructionSet(self._script_id)
                        src = ExprInstructionSet(self._script_id)

                        dst_data = data_span[expr[o].instruction_offset : expr[o].instruction_offset + expr[o].instruction_size]
                        src_data = data_span[expr[o + 1].instruction_offset : expr[o + 1].instruction_offset + expr[o + 1].instruction_size]

                        dst.get_instructions(dst_data)
                        src.get_instructions(src_data)

                        expr[o].expr_insts = dst
                        expr[o + 1].expr_insts = src
                        o += 2
                        continue

                elif cmd_name in ("STR", "INT", "FLT"):
                    # Local variable declaration
                    if o + 1 < len(expr):
                        dst = ExprInstructionSet(self._script_id)
                        src = ExprInstructionSet(self._script_id)

                        dst_data = data_span[expr[o].instruction_offset : expr[o].instruction_offset + expr[o].instruction_size]
                        src_data = data_span[expr[o + 1].instruction_offset : expr[o + 1].instruction_offset + expr[o + 1].instruction_size]

                        dst.get_instructions(dst_data)
                        src.get_instructions(src_data)

                        expr[o].expr_insts = dst
                        expr[o + 1].expr_insts = src

                        # Declare local array type
                        if isinstance(dst._inst, ArrayAccess):
                            aa = dst._inst
                            var_type = {"STR": 3, "FLT": 2}.get(cmd_name, 1)
                            aa.variable._var_info.type = var_type

                            # Extract dimensions from indices
                            dims = []
                            for d in aa.indices:
                                if isinstance(d, (ByteLiteral, ShortLiteral, IntLiteral, LongLiteral)):
                                    dims.append(int(d.value))
                                elif isinstance(d, DecimalLiteral):
                                    dims.append(int(d.value))
                                else:
                                    dims.append(0)  # Dynamic array not supported
                            aa.variable._var_info.dimensions = dims

                        elif isinstance(dst._inst, VariableAccess):
                            va = dst._inst
                            var_type = {"STR": 3, "FLT": 2}.get(cmd_name, 1)
                            va._var_info.type = var_type

                        elif isinstance(dst._inst, VariableRef):
                            vr = dst._inst
                            var_type = {"STR": 3, "FLT": 2}.get(cmd_name, 1)
                            vr._var_info.type = var_type

                        o += 2
                        continue

                elif cmd_name == "RETURNCODE":
                    # Return code with literal ID
                    expr[o].expr_insts = ExprInstructionSet(self._script_id, IntLiteral(expr[o].id))
                    o += 1
                    continue

                elif cmd_name == "LOOP":
                    # Remove modified var list
                    if len(expr) > o + 1:
                        del expr[o + 1]
                    string_expr = False

                elif cmd_name == "_":
                    string_expr = False

                # Process normal expressions
                if info is not None:
                    statement = AssignExprInstSet(self._script_id, info, expr[o].get_load_op())
                    expr[o].expr_insts = statement

                    if expr[o].instruction_size == 0:
                        o += 1
                        continue

                    # Handle potential buffer overflow
                    remaining_size = len(data_span) - expr[o].instruction_offset
                    instruction_size = min(expr[o].instruction_size, remaining_size)

                    if instruction_size != expr[o].instruction_size:
                        print(f"Warning: Expr({expr[o].instruction_offset})'s length doesn't match: ({instruction_size}/{expr[o].instruction_size}). Truncating...")

                    inst_data = data_span[expr[o].instruction_offset : expr[o].instruction_offset + instruction_size]
                    is_raw_string = string_expr and info.result_type == ExprEvalResult.RAW
                    statement.get_instructions(inst_data, is_raw_string)
                else:
                    if expr[o].instruction_size == 0:
                        o += 1
                        continue
                    raise ValueError("Unknown abnormal command with instruction(s).")

                o += 1
