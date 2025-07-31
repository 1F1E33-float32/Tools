from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class Opcode:
    id: int
    name: str

@dataclass
class Instruction:
    opcode: int
    operand: int

@dataclass
class Marker:
    count: int = 0

@dataclass
class Script:
    init_code: List[Instruction]
    code: List[Instruction]
    string_table: Dict[int, str]
    int_var_names: Dict[int, str]
    string_var_names: Dict[int, str]
    banks_params: Dict[int, Any]
    functions: Dict[int, Any]

@dataclass
class GlobalScript:
    int_var_names: Dict[int, str]
    string_var_names: Dict[int, str]
    string_table: Dict[int, str]
    code: List[Instruction]