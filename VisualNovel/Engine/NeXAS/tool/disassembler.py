from typing import Any, Callable, Dict, List

from ruamel.yaml import YAML

from .constants import FLAG_FUNC, FLAG_GLOBALVAR, FLAG_STRINGVAR
from .reader import ScriptReader
from .script_data import GlobalScript, Instruction, Opcode


class Disassembler:
    def __init__(self, config_path: str):
        self.yaml = YAML()
        self.yaml.default_flow_style = False
        self.yaml.indent(sequence=4, offset=2)
        with open(config_path, "r", encoding="utf-8") as file:
            self.config = self.yaml.load(file)
        self.reader = ScriptReader(self.config)
        self.opcodes = self.load_opcodes(self.config["opcodes"])
        self.native_functions = self.config["native_functions"] or {}
        self.script_functions = self.config["script_functions"] or {}
        self.opcodes_handlers = {
            "VAL": self.handler_val,
            "PUSH": self.handler_register,
            "PARAM": self.handler_param,
            "POP": self.handler_register,
            "CALL": self.handler_call,
            "LOAD": self.handler_load,
            "ADD": self.handler_add,
            "SUB": self.handler_without_operand,
            "MUL": self.handler_without_operand,
            "DIV": self.handler_without_operand,
            "MOD": self.handler_without_operand,
            "STORE": self.handler_variable_index,
            "OR": self.handler_without_operand,
            "AND": self.handler_without_operand,
            "BIT_OR": self.handler_without_operand,
            "BIT_AND": self.handler_without_operand,
            "XOR": self.handler_without_operand,
            "NOT": self.handler_without_operand,
            "CMP_LE": self.handler_without_operand,
            "CMP_GE": self.handler_without_operand,
            "CMP_LT": self.handler_without_operand,
            "CMP_GT": self.handler_without_operand,
            "CMP_EQ": self.handler_type,
            "CMP_NE": self.handler_type,
            "START": self.handler_simple,
            "END": self.handler_without_operand,
            "MARKER": self.handler_without_operand,
            "INC": self.handler_variable_index,
            "DEC": self.handler_variable_index,
            "UNK_41": self.handler_simple,
            "CMP_ZERO": self.handler_without_operand,
            "LINENO": self.handler_simple,
            "SAR": self.handler_without_operand,
            "SHL": self.handler_without_operand,
            "SHR": self.handler_without_operand,
            "LD_ADD": self.handler_variable_index,
            "LD_SUB": self.handler_variable_index,
            "LD_MUL": self.handler_variable_index,
            "LD_DIV": self.handler_variable_index,
            "LD_MOD": self.handler_variable_index,
            "LD_OR": self.handler_variable_index,
            "LD_AND": self.handler_variable_index,
            "LD_XOR": self.handler_variable_index,
            "LD_SAR": self.handler_variable_index,
            "LD_SHL": self.handler_variable_index,
            "LD_SHR": self.handler_variable_index,
            "UNK_61": self.handler_simple,
            "UNK_62": self.handler_simple,
            "TO_STRING": self.handler_register,
            "RETURN": self.handler_type,
            "JMP": self.handler_jump,
            "JMP_IF_FALSE": self.handler_jump,
            "JMP_IF_TRUE": self.handler_jump,
            "TO_INT": self.handler_register,
            "PARAM_MIN": self.handler_without_operand,
            "PARAM_MAX": self.handler_without_operand,
            "PARAM_FLAG": self.handler_without_operand,
        }
        self.registers = [0, 0]
        self.stack: List[Any] = []
        self.global_data = GlobalScript(int_var_names={}, string_var_names={}, string_table={}, code=[])

    def load_opcodes(self, opcodes_config: Dict[int, str]) -> Dict[int, Opcode]:
        opcodes = {}
        for id, name in opcodes_config.items():
            opcodes[id] = Opcode(id, name)
        return opcodes

    def get_opcode(self, id: int) -> Opcode:
        return self.opcodes[id]

    def get_opcode_handler(self, name: str) -> Callable[..., dict]:
        return self.opcodes_handlers[name]

    def find_labels(self, instructions: List[Instruction]) -> Dict[int, str]:
        labels: Dict[int, str] = {}
        for addr, ins in enumerate(instructions):
            mnemonic = self.get_opcode(ins.opcode).name
            if addr == 0 or mnemonic == "START":
                self.make_label(labels, addr)
            if mnemonic in ("JMP", "JMP_IF_FALSE", "JMP_IF_TRUE"):
                self.make_label(labels, addr + 1)
                self.make_label(labels, ins.operand + 1)
        return labels

    def make_label(self, labels: Dict[int, str], addr: int) -> None:
        if addr not in labels:
            labels[addr] = f"LABEL_{len(labels) + 1}"

    def disassemble(self, script_path: str) -> None:
        script = self.reader.read_script_from_file(script_path)
        data = {
            "string_table": script.string_table,
            "int_var_names": script.int_var_names,
            "string_var_names": script.string_var_names,
            "banks_params": script.banks_params,
        }
        disassembled_script = {
            "init_code": self.disassemble_code(script.init_code, data),
            "code": self.disassemble_code(script.code, data),
            **data,
            "functions": self.disassemble_functions(script.functions),
        }
        return disassembled_script

    def load_and_disassemble_global(self, global_script_path: str) -> None:
        self.global_data = self.reader.read_global_script_from_file(global_script_path)

    def disassemble_code(self, instructions: List[Instruction], data: Dict[str, Any]) -> List[dict]:
        """
        Instead of a plain text string, we now return a list of blocks.
        Each block is a dictionary with an optional label and a list of instruction entries.
        """
        labels = self.find_labels(instructions)
        blocks = []
        current_block = None

        for i, ins in enumerate(instructions):
            if i in labels:
                # Start a new block whenever a label is encountered.
                if current_block is not None:
                    blocks.append(current_block)
                current_block = {"label": labels[i], "instructions": []}
            # Get the opcode mnemonic and then call its handler to return structured data.
            mnemonic = self.get_opcode(ins.opcode).name
            handler = self.get_opcode_handler(mnemonic)
            instr_dict = handler(data=data, labels=labels, mnemonic=mnemonic, ins=ins, addr=i)
            current_block["instructions"].append(instr_dict)
        if current_block is not None:
            blocks.append(current_block)
        # If there is a label at the very end (after all instructions), create an empty block.
        if len(instructions) in labels:
            blocks.append({"label": labels[len(instructions)], "instructions": []})
        return blocks

    def disassemble_functions(self, functions: Dict[int, Any]) -> Dict[str, Any]:
        disassembled_functions = {}
        for func in functions:
            code = functions[func]["code"]
            data = {
                "string_table": functions[func]["string_table"],
                "int_var_names": functions[func]["int_var_names"],
                "string_var_names": functions[func]["string_var_names"],
            }
            disassembled_functions[f"FUNC_{hex(func)}"] = {"code": self.disassemble_code(code, data), **data}
        return disassembled_functions

    # --- Handler methods now return structured dictionaries ---

    def handler_val(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        data = kwargs["data"]
        # Update register
        self.registers[0] = ins.operand
        operand = ins.operand & 0xFFFFFFFF

        instr = {"mnemonic": mnemonic, "operand_raw": ins.operand, "operand_display": None, "comment": ""}
        is_string_variable, is_global_string_variable, is_global_int_variable = self.is_variable(data, operand)
        if is_global_string_variable:
            instr["operand_display"] = f"[GLOBAL_STRING_VAR] {operand ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)}"
        elif is_global_int_variable:
            instr["operand_display"] = f"[GLOBAL_INT_VAR] {operand ^ FLAG_GLOBALVAR}"
        elif is_string_variable:
            instr["operand_display"] = f"[STRING_VAR] {operand ^ FLAG_STRINGVAR}"
        else:
            instr["operand_display"] = f"{ins.operand}"
        return instr

    def handler_register(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        instr = {"mnemonic": mnemonic, "operand_display": f"$R{ins.operand}", "comment": ""}
        if mnemonic == "PUSH":
            self.stack.append(self.registers[ins.operand])
        elif mnemonic == "POP":
            self.registers[ins.operand] = self.stack.pop()
        return instr

    def handler_param(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        data = kwargs["data"]
        result = {"mnemonic": mnemonic, "operand": ins.operand, "param_type": None, "comment": ""}
        if ins.operand == 0:
            result["param_type"] = "@INT"
        elif ins.operand == 1:
            result["param_type"] = "@STRING"
            register_zero = self.registers[0] & 0xFFFFFFFF
            if register_zero & FLAG_STRINGVAR:
                if register_zero & FLAG_GLOBALVAR:
                    name = self.global_data.string_var_names.get(register_zero ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR), f"var_{register_zero ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)}")
                    result["comment"] = f"string @ [GLOBAL_STRING_VAR] {name}"
                else:
                    name = data["string_var_names"].get(register_zero ^ FLAG_STRINGVAR, f"var_{register_zero ^ FLAG_STRINGVAR}")
                    result["comment"] = f"string @ [STRING_VAR] {name}"
            else:
                name = data["string_table"].get(self.registers[0], "Invalid string (Likely calculated string index)")
                result["comment"] = f"[{self.registers[0]}]{name}"
        return result

    def handler_call(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        param_count = (ins.operand >> 16) & 0xFFFF
        result = {"mnemonic": mnemonic, "operand": ins.operand, "parameter_count": param_count, "function_type": None, "function": None, "comment": ""}
        if ins.operand & FLAG_FUNC:
            result["function_type"] = "FUNC"
            func_number = (ins.operand ^ FLAG_FUNC) & 0xFFFF
            result["function"] = self.script_functions.get(func_number, f"FUNC_{hex(func_number)}")
        else:
            result["function_type"] = "NATIVE"
            func_number = ins.operand & 0xFFFF
            result["function"] = self.native_functions.get(func_number, f"CMD_{hex(func_number)}")
        return result

    def handler_load(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        data = kwargs["data"]
        register = self.registers[ins.operand] & 0xFFFFFFFF

        result = {"mnemonic": mnemonic, "handler": "handler_load", "register": ins.operand, "resolved_value": register, "resolved_type": None, "resolved_name": None, "comment": ""}
        is_string_variable, is_global_string_variable, is_global_int_variable = self.is_variable(data, register)
        if is_global_string_variable:
            result["resolved_type"] = "GLOBAL_STRING_VAR"
            result["resolved_name"] = self.global_data.string_var_names.get(register ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR), f"var_{register ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)}")
        elif is_global_int_variable:
            result["resolved_type"] = "GLOBAL_INT_VAR"
            result["resolved_name"] = self.global_data.int_var_names.get(register ^ FLAG_GLOBALVAR, f"var_{register ^ FLAG_GLOBALVAR}")
        elif is_string_variable:
            result["resolved_type"] = "STRING_VAR"
            result["resolved_name"] = data["string_var_names"].get(register ^ FLAG_STRINGVAR, f"var_{register ^ FLAG_STRINGVAR}")
        else:
            result["resolved_type"] = "INT_VAR"
            result["resolved_name"] = data["int_var_names"].get(register, f"var_{register}")
        return result

    def handler_add(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        result = {"mnemonic": mnemonic, "operand": ins.operand, "param_type": None, "comment": ""}
        if ins.operand == 0:
            result["param_type"] = "@INT"
        elif ins.operand == 1:
            result["param_type"] = "@STRING"
            # Note: the original code added a comment for NEXT PARAM (@STRING)
            result["comment"] = "Next PARAM @STRING comment will be invalid"
        return result

    def handler_without_operand(self, **kwargs) -> dict:
        mnemonic = kwargs["mnemonic"]
        return {"mnemonic": mnemonic, "operand": None, "comment": ""}

    def handler_variable_index(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        data = kwargs["data"]

        result = {"mnemonic": mnemonic, "operand": ins.operand, "variable_info": {}, "comment": ""}
        if ins.operand == -1:
            result["variable_info"] = {"value": -1}
        else:
            operand = ins.operand & 0xFFFFFFFF
            is_string_variable, is_global_string_variable, is_global_int_variable = self.is_variable(data, operand)
            if is_global_string_variable:
                result["variable_info"]["type"] = "GLOBAL_STRING_VAR"
                result["variable_info"]["index"] = operand ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)
                result["variable_info"]["name"] = self.global_data.string_var_names.get(operand ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR), f"var_{operand ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)}")
            elif is_global_int_variable:
                result["variable_info"]["type"] = "GLOBAL_INT_VAR"
                result["variable_info"]["index"] = operand ^ FLAG_GLOBALVAR
                result["variable_info"]["name"] = self.global_data.int_var_names.get(operand ^ FLAG_GLOBALVAR, f"var_{operand ^ FLAG_GLOBALVAR}")
            elif is_string_variable:
                result["variable_info"]["type"] = "STRING_VAR"
                result["variable_info"]["index"] = operand ^ FLAG_STRINGVAR
                result["variable_info"]["name"] = data["string_var_names"].get(operand ^ FLAG_STRINGVAR, f"var_{operand ^ FLAG_STRINGVAR}")
            else:
                result["variable_info"]["type"] = "INT_VAR"
                result["variable_info"]["index"] = ins.operand
                result["variable_info"]["name"] = data["int_var_names"].get(ins.operand, f"var_{ins.operand}")
        return result

    def handler_type(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        result = {"mnemonic": mnemonic, "operand": ins.operand, "param_type": None, "comment": ""}
        if ins.operand == 0:
            result["param_type"] = "@INT"
        elif ins.operand in (1, 2):
            result["param_type"] = "@STRING"
        return result

    def handler_simple(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        return {"mnemonic": mnemonic, "operand": ins.operand, "comment": ""}

    def handler_jump(self, **kwargs) -> dict:
        ins = kwargs["ins"]
        mnemonic = kwargs["mnemonic"]
        addr = kwargs["addr"]
        labels = kwargs["labels"]
        result = {"mnemonic": mnemonic, "target_label": labels.get(ins.operand + 1, ""), "current_addr": addr, "comment": ""}
        if mnemonic == "JMP" and ins.operand == addr:
            result["comment"] = "Filler"
        return result

    def is_variable(self, data: Dict[str, Any], value: int) -> tuple[bool, bool, bool]:
        is_string_variable = len(data["string_var_names"]) > 0 and (value ^ FLAG_STRINGVAR) < len(data["string_var_names"]) and (value ^ FLAG_STRINGVAR) >= 0
        is_global_string_variable = len(self.global_data.string_var_names) > 0 and (value ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)) < len(self.global_data.string_var_names) and (value ^ (FLAG_GLOBALVAR | FLAG_STRINGVAR)) >= 0
        is_global_int_variable = len(self.global_data.int_var_names) > 0 and (value ^ FLAG_GLOBALVAR) < len(self.global_data.int_var_names) and (value ^ FLAG_GLOBALVAR) >= 0

        return (is_string_variable, is_global_string_variable, is_global_int_variable)
