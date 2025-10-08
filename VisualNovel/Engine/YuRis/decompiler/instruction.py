import struct
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import List, Optional


class Opcode(IntEnum):
    RAW_OPERAND = ord(" ")  # 0x20
    NOT_EQUAL = ord("!")  # 0x21
    MODULO = ord("%")  # 0x25
    LOGICAL_AND = ord("&")  # 0x26
    ARRAY_ACCESS = ord(")")  # 0x29
    MULTIPLY = ord("*")  # 0x2A
    ADD = ord("+")  # 0x2B
    NOP = ord(",")  # 0x2C
    SUBTRACT = ord("-")  # 0x2D
    DIVIDE = ord("/")  # 0x2F
    LESS = ord("<")  # 0x3C
    EQUAL = ord("=")  # 0x3D
    GREATER = ord(">")  # 0x3E
    BITWISE_AND = ord("A")  # 0x41
    PUSH_BYTE = ord("B")  # 0x42
    PUSH_DOUBLE = ord("F")  # 0x46
    LOAD_VARIABLE = ord("H")  # 0x48
    PUSH_INT = ord("I")  # 0x49
    PUSH_LONG = ord("L")  # 0x4C
    PUSH_STRING = ord("M")  # 0x4D
    BITWISE_OR = ord("O")  # 0x4F
    NEGATE = ord("R")  # 0x52
    LESS_EQUAL = ord("S")  # 0x53
    LOAD_VARIABLE_REF = ord("V")  # 0x56
    PUSH_SHORT = ord("W")  # 0x57
    GREATER_EQUAL = ord("Z")  # 0x5A
    BITWISE_XOR = ord("^")  # 0x5E
    TO_NUMBER = ord("i")  # 0x69
    TO_STRING = ord("s")  # 0x73
    LOAD_VARIABLE_REF2 = ord("v")  # 0x76
    LOGICAL_OR = ord("|")  # 0x7C


class VariableLoadMode(IntEnum):
    BACKTICK = ord("`")
    POUND = ord("#")
    DOLLAR = ord("$")  # Undocumented but appears in data
    AT = ord("@")


class Instruction(ABC):
    @staticmethod
    def get_instruction(script_id: int, data: bytes, offset: int) -> tuple["Instruction", int]:
        opcode = Opcode(data[offset])
        operand_length = struct.unpack("<H", data[offset + 1 : offset + 3])[0]
        operand_data = data[offset + 3 : offset + 3 + operand_length]

        new_offset = offset + 3 + operand_length

        # Arithmetic operators
        if opcode in (Opcode.ADD, Opcode.SUBTRACT, Opcode.MULTIPLY, Opcode.DIVIDE, Opcode.MODULO):
            inst = ArithmeticOperator(None, None, ArithmeticOperator.Type(opcode))
            return inst, new_offset

        # Logical operators
        if opcode in (Opcode.LOGICAL_AND, Opcode.LOGICAL_OR, Opcode.BITWISE_XOR, Opcode.BITWISE_AND, Opcode.BITWISE_OR):
            inst = LogicalOperator(None, None, LogicalOperator.Type(opcode))
            return inst, new_offset

        # Relational operators
        if opcode in (Opcode.EQUAL, Opcode.NOT_EQUAL, Opcode.LESS, Opcode.GREATER, Opcode.LESS_EQUAL, Opcode.GREATER_EQUAL):
            inst = RelationalOperator(None, None, RelationalOperator.Type(opcode))
            return inst, new_offset

        # Unary operators
        if opcode in (Opcode.NEGATE, Opcode.TO_STRING, Opcode.TO_NUMBER):
            inst = UnaryOperator(None, UnaryOperator.Type(opcode))
            return inst, new_offset

        # Array access
        if opcode == Opcode.ARRAY_ACCESS:
            return ArrayAccess(None, None), new_offset

        # Literals
        if opcode == Opcode.PUSH_BYTE:
            assert operand_length == 1
            return ByteLiteral(struct.unpack("b", operand_data)[0]), new_offset

        if opcode == Opcode.PUSH_DOUBLE:
            assert operand_length == 8
            return DecimalLiteral(struct.unpack("<d", operand_data)[0]), new_offset

        if opcode == Opcode.PUSH_SHORT:
            assert operand_length == 2
            return ShortLiteral(struct.unpack("<h", operand_data)[0]), new_offset

        if opcode == Opcode.PUSH_INT:
            assert operand_length == 4
            return IntLiteral(struct.unpack("<i", operand_data)[0]), new_offset

        if opcode == Opcode.PUSH_LONG:
            assert operand_length == 8
            return LongLiteral(struct.unpack("<q", operand_data)[0]), new_offset

        if opcode == Opcode.PUSH_STRING:
            from .extensions import Extensions

            return StringLiteral(operand_data.decode(Extensions.get_default_encoding(), errors="replace")), new_offset

        # Variable access
        if opcode == Opcode.LOAD_VARIABLE:
            assert operand_length == 3
            mode = VariableLoadMode(operand_data[0])
            var_id = struct.unpack("<h", operand_data[1:3])[0]
            return VariableAccess(script_id, mode, var_id), new_offset

        if opcode == Opcode.LOAD_VARIABLE_REF:
            assert operand_length == 3
            mode = VariableLoadMode(operand_data[0])
            var_id = struct.unpack("<h", operand_data[1:3])[0]
            return VariableRef(script_id, mode, var_id, False), new_offset

        if opcode == Opcode.LOAD_VARIABLE_REF2:
            assert operand_length == 3
            mode = VariableLoadMode(operand_data[0])
            var_id = struct.unpack("<h", operand_data[1:3])[0]
            return VariableRef(script_id, mode, var_id, True), new_offset

        if opcode == Opcode.NOP:
            return Nop(), new_offset

        raise ValueError(f"Invalid opcode: {opcode:02X}")

    @abstractmethod
    def __str__(self) -> str:
        pass


class BinaryOperator(Instruction):
    def __init__(self, left: Optional[Instruction], right: Optional[Instruction], operator: IntEnum):
        self.left = left
        self.right = right
        self.operator = operator

    @abstractmethod
    def get_operator_str(self, op_type: IntEnum) -> str:
        pass

    def __str__(self) -> str:
        return f"({self.left}){self.get_operator_str(self.operator)}({self.right})"


class ArithmeticOperator(BinaryOperator):
    class Type(IntEnum):
        ADD = Opcode.ADD
        SUBTRACT = Opcode.SUBTRACT
        MULTIPLY = Opcode.MULTIPLY
        DIVIDE = Opcode.DIVIDE
        MODULO = Opcode.MODULO

    def __init__(self, left: Optional[Instruction], right: Optional[Instruction], op: Type):
        super().__init__(left, right, op)
        self.negate = False

    def get_operator_str(self, op_type: IntEnum) -> str:
        ops = {self.Type.ADD: "+", self.Type.SUBTRACT: "-", self.Type.MULTIPLY: "*", self.Type.DIVIDE: "/", self.Type.MODULO: "%"}
        return ops.get(op_type, "?")

    def __str__(self) -> str:
        if self.negate:
            return f"(-({super().__str__()}))"
        return super().__str__()


class LogicalOperator(BinaryOperator):
    class Type(IntEnum):
        LOGICAL_AND = Opcode.LOGICAL_AND
        LOGICAL_OR = Opcode.LOGICAL_OR
        BITWISE_XOR = Opcode.BITWISE_XOR
        BITWISE_AND = Opcode.BITWISE_AND
        BITWISE_OR = Opcode.BITWISE_OR

    def __init__(self, left: Optional[Instruction], right: Optional[Instruction], op: Type):
        super().__init__(left, right, op)

    def get_operator_str(self, op_type: IntEnum) -> str:
        ops = {self.Type.LOGICAL_AND: "&&", self.Type.LOGICAL_OR: "||", self.Type.BITWISE_XOR: "^", self.Type.BITWISE_AND: "&", self.Type.BITWISE_OR: "|"}
        return ops.get(op_type, "?")


class RelationalOperator(BinaryOperator):
    class Type(IntEnum):
        EQUAL = Opcode.EQUAL
        NOT_EQUAL = Opcode.NOT_EQUAL
        LESS = Opcode.LESS
        GREATER = Opcode.GREATER
        LESS_EQUAL = Opcode.LESS_EQUAL
        GREATER_EQUAL = Opcode.GREATER_EQUAL

    def __init__(self, left: Optional[Instruction], right: Optional[Instruction], op: Type):
        super().__init__(left, right, op)

    def get_operator_str(self, op_type: IntEnum) -> str:
        ops = {self.Type.EQUAL: "==", self.Type.NOT_EQUAL: "!=", self.Type.LESS: "<", self.Type.GREATER: ">", self.Type.LESS_EQUAL: "<=", self.Type.GREATER_EQUAL: ">="}
        return ops.get(op_type, "?")


class UnaryOperator(Instruction):
    class Type(IntEnum):
        NEGATE = Opcode.NEGATE
        TO_STRING = Opcode.TO_STRING
        TO_NUMBER = Opcode.TO_NUMBER

    def __init__(self, operand: Optional[Instruction], op: Type):
        self.operand = operand
        self.operator = op

    def __str__(self) -> str:
        if self.operator == self.Type.NEGATE:
            return f"-({self.operand})"
        elif self.operator == self.Type.TO_STRING:
            return f"str({self.operand})"
        elif self.operator == self.Type.TO_NUMBER:
            return f"int({self.operand})"
        return f"?({self.operand})"


class ArrayAccess(Instruction):
    def __init__(self, variable: Optional["VariableRef"], indices: Optional[List[Instruction]] = None):
        self.variable = variable
        self.indices = indices if indices is not None else []
        self.negate = False

    def __str__(self) -> str:
        indices_str = ",".join(str(idx) for idx in self.indices)
        if self.negate:
            return f"(-{self.variable}({indices_str}))"
        return f"{self.variable}({indices_str})"


# Literal instructions
class ByteLiteral(Instruction):
    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class ShortLiteral(Instruction):
    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class IntLiteral(Instruction):
    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class LongLiteral(Instruction):
    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class DecimalLiteral(Instruction):
    def __init__(self, value: float):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class StringLiteral(Instruction):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        # Escape special characters
        escaped = self.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
        return f'"{escaped}"'


class RawStringLiteral(Instruction):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return self.value


class Nop(Instruction):
    def __str__(self) -> str:
        return "nop"


class VariableAccess(Instruction):
    def __init__(self, script_id: int, mode: VariableLoadMode, var_id: int):
        from .ysvr import YSVR

        self.script_id = script_id
        self.mode = mode
        self.var_id = var_id
        self._var_info = YSVR.get_variable(script_id, var_id)
        self.index: Optional[Instruction] = None
        self.negate = False

    def __str__(self) -> str:
        from .ysvr import YSVR

        prefix = {VariableLoadMode.BACKTICK: "`", VariableLoadMode.POUND: "#", VariableLoadMode.AT: "@"}.get(self.mode, "")

        var_name = YSVR.get_decompiled_var_name(self._var_info)

        if self.negate:
            return f"(-{chr(self.mode)}{var_name})"

        if self.index is not None:
            return f"{prefix}{var_name}[{self.index}]"
        else:
            return f"{prefix}{var_name}"


class VariableRef(Instruction):
    def __init__(self, script_id: int, mode: VariableLoadMode, var_id: int, is_ref2: bool):
        from .ysvr import YSVR

        self.script_id = script_id
        self.mode = mode
        self.var_id = var_id
        self.is_ref2 = is_ref2
        self._var_info = YSVR.get_variable(script_id, var_id)
        self.index: Optional[Instruction] = None

    def __str__(self) -> str:
        from .ysvr import YSVR

        prefix = {VariableLoadMode.BACKTICK: "`", VariableLoadMode.POUND: "#", VariableLoadMode.AT: "@"}.get(self.mode, "")

        var_name = YSVR.get_decompiled_var_name(self._var_info)

        if self.index is not None:
            return f"{prefix}{var_name}[{self.index}]"
        else:
            return f"{prefix}{var_name}"


class KeywordRef(Instruction):
    def __init__(self, name: Optional[str]):
        self.name = name

    def __str__(self) -> str:
        return self.name if self.name else ""
