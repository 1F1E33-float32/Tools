from enum import IntEnum
from io import StringIO
from typing import Any, List

from .extensions import BinaryReaderHelper


class VariableType(IntEnum):
    VOID = 0
    INTEGER = 1
    DECIMAL = 2
    STRING = 3


class VariableScope(IntEnum):
    LOCAL = 0
    GLOBAL = 1
    SCRIPT = 2
    UNKNOWN = 3


class Variable:
    def __init__(self, scope: VariableScope, script_index: int, variable_id: int, var_type: int, dimensions: List[int], value: Any):
        self.scope = scope
        self.script_index = script_index
        self.variable_id = variable_id
        self.type = var_type
        self.dimensions = dimensions
        self.value = value

    def __str__(self) -> str:
        dims_str = ",".join(str(d) for d in self.dimensions)
        return f"{self.scope.name}.{self.variable_id} -> {self.type}({dims_str})"


class YSVR:
    MAGIC = 0x52565359  # 'YSVR'

    # Static class variable
    _variables: List[Variable] = []

    @staticmethod
    def enumerate_variables() -> List[Variable]:
        return YSVR._variables

    @staticmethod
    def load(file_path: str):
        with open(file_path, "rb") as f:
            YSVR._read(BinaryReaderHelper(f))

    @staticmethod
    def _read(reader: BinaryReaderHelper):
        # Import here to avoid circular dependency
        from .instruction import Instruction

        # Read and validate magic number
        magic = reader.read_int32()
        if magic != YSVR.MAGIC:
            raise ValueError("Not a valid YSVR file.")

        # Read version
        ver = reader.read_int32()

        # Read variable count
        count = reader.read_uint16()

        # Read variables
        YSVR._variables = []
        for i in range(count):
            scope = VariableScope(reader.read_byte())

            # Workaround for version > 454
            if ver > 454:
                reader.read_byte()

            script_index = reader.read_int16()
            variable_id = reader.read_int16()
            var_type = reader.read_byte()
            dimension_count = reader.read_byte()

            dimensions = []
            for o in range(dimension_count):
                dimensions.append(reader.read_uint32())

            # Read value based on type
            value = None
            if var_type == 1:  # Integer
                value = reader.read_int64()
            elif var_type == 2:  # Decimal
                value = reader.read_double()
            elif var_type == 3:  # String (instruction)
                length = reader.read_uint16()
                if length > 0:
                    data = reader.read_bytes(length)
                    value = Instruction.get_instruction(0, data, 0)

            YSVR._variables.append(Variable(scope, script_index, variable_id, var_type, dimensions, value))

    @staticmethod
    def get_variable(script_index: int, variable_id: int) -> Variable:
        # Try to find exact match
        for v in YSVR._variables:
            if v.script_index == script_index and v.variable_id == variable_id:
                return v

        # Try to find by variable ID only
        for v in YSVR._variables:
            if v.variable_id == variable_id:
                return v

        # Create new local variable if not found
        ret = Variable(VariableScope.LOCAL, script_index, variable_id, 0, [], None)
        YSVR._variables.append(ret)
        return ret

    @staticmethod
    def get_decompiled_var_name(variable: Variable) -> str:
        from .yscd import YSCD

        if variable.scope == VariableScope.GLOBAL and variable.variable_id < len(YSCD.get_reserved_vars()):
            return YSCD.get_reserved_vars()[variable.variable_id].name

        return f"{variable.scope.name.lower()}.{variable.variable_id}"

    @staticmethod
    def write_global_var_decl(writer: StringIO):
        from .yscd import YSCD

        reserved_count = len(YSCD.get_reserved_vars())

        for variable in YSVR._variables:
            if variable.scope == VariableScope.GLOBAL and variable.variable_id >= reserved_count:
                # Format dimensions
                dem = ""
                if len(variable.dimensions) > 0:
                    dims_str = ",".join(str(d) for d in variable.dimensions)
                    dem = f"({dims_str})"

                # Format value
                val_str = ""
                if variable.value is not None:
                    val_str = f"={variable.value}"

                var_name = YSVR.get_decompiled_var_name(YSVR.get_variable(0, variable.variable_id))
                v = f"{var_name}{dem}{val_str}"

                # Write based on type
                if variable.type == 1:  # Integer
                    writer.write(f"G_INT[@{v}]\n")
                elif variable.type == 2:  # Decimal
                    writer.write(f"G_FLT[@{v}]\n")
                elif variable.type == 3:  # String
                    writer.write(f"G_STR[${v}]\n")
