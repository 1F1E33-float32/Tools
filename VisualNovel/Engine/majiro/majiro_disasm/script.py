from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .instruction import Instruction


class MjoScriptRepresentation(Enum):
    INSTRUCTION_LIST = "instruction_list"
    CONTROL_FLOW_GRAPH = "control_flow_graph"
    SSA_GRAPH = "ssa_graph"
    SYNTAX_TREE = "syntax_tree"
    IN_TRANSITION = "in_transition"


@dataclass
class FunctionIndexEntry:
    name_hash: int
    offset: int

    def to_dict(self) -> dict:
        return {
            "name_hash": self.name_hash,
            "offset": self.offset
        }


@dataclass
class MjoScript:
    representation: MjoScriptRepresentation = MjoScriptRepresentation.INSTRUCTION_LIST
    enable_read_mark: bool = False

    # InstructionList representation
    instructions: Optional[List[Instruction]] = None
    function_index: Optional[List[FunctionIndexEntry]] = None
    entry_point_offset: Optional[int] = None

    # Externalized strings (for translation)
    externalized_strings: Optional[Dict[str, str]] = None

    def instruction_index_from_offset(self, offset: int) -> Optional[int]:
        if not self.instructions:
            return None

        for i, instr in enumerate(self.instructions):
            if instr.offset == offset:
                return i
        return None

    def to_dict(self) -> dict:
        result = {
            "representation": self.representation.value,
            "enable_read_mark": self.enable_read_mark
        }
        
        if self.entry_point_offset is not None:
            result["entry_point_offset"] = self.entry_point_offset
        
        if self.function_index:
            result["function_index"] = [entry.to_dict() for entry in self.function_index]
        
        if self.instructions:
            result["instructions"] = [instr.to_dict() for instr in self.instructions]
        
        if self.externalized_strings:
            result["externalized_strings"] = self.externalized_strings
        
        return result
