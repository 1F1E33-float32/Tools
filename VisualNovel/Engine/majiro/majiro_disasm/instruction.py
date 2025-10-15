from dataclasses import dataclass
from typing import List, Optional

from .flags import MjoType
from .opcode import Opcode


@dataclass
class Instruction:
    opcode: Opcode
    offset: Optional[int] = None
    size: Optional[int] = None

    # Operands
    flags: int = 0
    hash: int = 0
    var_offset: int = 0
    type_list: Optional[List[MjoType]] = None
    string: Optional[str] = None
    external_key: Optional[str] = None
    int_value: int = 0
    float_value: float = 0.0
    argument_count: int = 0
    line_number: int = 0
    jump_offset: Optional[int] = None
    switch_offsets: Optional[List[int]] = None

    # Properties for instruction type checking
    @property
    def is_jump(self) -> bool:
        return self.opcode.is_jump

    @property
    def is_unconditional_jump(self) -> bool:
        return self.opcode.value == 0x82C

    @property
    def is_switch(self) -> bool:
        return self.opcode.value == 0x850

    @property
    def is_return(self) -> bool:
        return self.opcode.value == 0x82B

    @property
    def is_arg_check(self) -> bool:
        return self.opcode.value == 0x836

    @property
    def is_alloca(self) -> bool:
        return self.opcode.value == 0x829

    @property
    def is_text(self) -> bool:
        return self.opcode.value == 0x840

    @property
    def is_proc(self) -> bool:
        return self.opcode.value == 0x841

    @property
    def is_ctrl(self) -> bool:
        return self.opcode.value == 0x842

    @property
    def is_pop(self) -> bool:
        return self.opcode.value == 0x82F

    @property
    def is_bsel_clr(self) -> bool:
        return self.opcode.value == 0x844

    @property
    def is_line(self) -> bool:
        return self.opcode.value == 0x83A

    @property
    def is_syscall(self) -> bool:
        return self.opcode.value in (0x834, 0x835)

    @property
    def is_call(self) -> bool:
        return self.opcode.value in (0x80F, 0x810)

    @property
    def is_load(self) -> bool:
        return self.opcode.mnemonic.startswith("ld")

    @property
    def is_store(self) -> bool:
        return self.opcode.mnemonic.startswith("st")

    def __str__(self) -> str:
        return f"{self.opcode.mnemonic}"

    def to_dict(self) -> dict:
        from .known_names import KnownNames
        
        result = {
            "opcode": {
                "value": self.opcode.value,
                "mnemonic": self.opcode.mnemonic,
            }
        }
        
        if self.offset is not None:
            result["offset"] = self.offset
        if self.size is not None:
            result["size"] = self.size
        if self.flags != 0:
            result["flags"] = self.flags
        if self.hash != 0:
            result["hash"] = self.hash
            
            # 添加已解析的名称信息
            if self.is_syscall:
                name = KnownNames.get_syscall_name(self.hash)
                if name:
                    result["resolved_name"] = f"${name}@MAJIRO_INTER"
            elif self.is_call:
                name = KnownNames.get_function_name(self.hash)
                if name:
                    result["resolved_name"] = name
            elif self.is_load or self.is_store:
                name = KnownNames.get_variable_name(self.hash)
                if name:
                    result["resolved_name"] = name
                    
        if self.var_offset != 0:
            result["var_offset"] = self.var_offset
        if self.type_list:
            result["type_list"] = [t.name.lower() for t in self.type_list]
        if self.string is not None:
            result["string"] = self.string
        if self.external_key is not None:
            result["external_key"] = self.external_key
        if self.int_value != 0:
            result["int_value"] = self.int_value
        if self.float_value != 0.0:
            result["float_value"] = self.float_value
        if self.argument_count != 0:
            result["argument_count"] = self.argument_count
        if self.line_number != 0:
            result["line_number"] = self.line_number
        if self.jump_offset is not None:
            result["jump_offset"] = self.jump_offset
        if self.switch_offsets:
            result["switch_offsets"] = self.switch_offsets
            
        return result
