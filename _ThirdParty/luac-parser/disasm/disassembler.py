import json
import math
from typing import Any, Dict, List, Optional, Tuple

from .core import LUA51, LUA52, LUA53, LUA54, LuaBytecode, LuaChunk, LuaConstant, LuaNumber, LuaVersion


class Disassembler:
    def __init__(self, version: LuaVersion):
        self.version = version

    def disassemble_to_txt(self, bytecode: LuaBytecode) -> str:
        lines: List[str] = []
        lines.append("=== Lua Bytecode Disassembly ===")
        lines.append(f"Version: {self.version}")
        lines.append(f"Endianness: {'Big' if bytecode.header.big_endian else 'Little'}")
        lines.append("")
        self._disassemble_chunk_txt(bytecode.main_chunk, lines, 0, "main")
        return "\n".join(lines)

    def disassemble_to_json(self, bytecode: LuaBytecode) -> str:
        functions: List[Dict[str, Any]] = []
        self._collect_functions(bytecode.main_chunk, functions, "main")
        payload = {
            "version": str(self.version),
            "endianness": "Big" if bytecode.header.big_endian else "Little",
            "functions": functions,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def disassemble(self, bytecode: LuaBytecode) -> str:
        return self.disassemble_to_txt(bytecode)

    def _constant_to_json(self, constant: LuaConstant) -> Tuple[str, Any]:
        if constant.kind == "null":
            return "Null", None
        if constant.kind == "bool":
            return "Boolean", bool(constant.value)
        if constant.kind == "number":
            number: LuaNumber = constant.value
            if number.is_integer:
                return "Integer", int(number.value)
            if isinstance(number.value, float) and math.isfinite(number.value):
                return "Number", float(number.value)
            return "Number", str(number.value)
        if constant.kind == "string":
            try:
                text = constant.value.decode("utf-8")
            except UnicodeDecodeError:
                text = constant.value.decode("utf-8", errors="replace")
            return "String", text
        return constant.kind.capitalize(), constant.value

    def _collect_functions(self, chunk: LuaChunk, functions: List[Dict[str, Any]], name: str) -> None:
        constants = []
        for index, constant in enumerate(chunk.constants):
            const_type, value = self._constant_to_json(constant)
            constants.append({"index": index, "type": const_type, "value": value})

        instructions = []
        for pc, inst in enumerate(chunk.instructions):
            line = chunk.source_lines[pc][0] if pc < len(chunk.source_lines) else 0
            detailed = self._disassemble_instruction_detailed(inst, pc, chunk)
            if detailed is None:
                continue
            opcode, operands = detailed
            instructions.append({"pc": pc, "line": line, "opcode": opcode, "operands": operands})

        functions.append(
            {
                "name": name,
                "line_defined": chunk.line_defined,
                "last_line_defined": chunk.last_line_defined,
                "num_params": chunk.num_params,
                "max_stack": chunk.max_stack,
                "num_upvalues": chunk.num_upvalues,
                "constants": constants,
                "instructions": instructions,
            }
        )

        for index, proto in enumerate(chunk.prototypes):
            proto_name = f"{name}/<{index}>"
            self._collect_functions(proto, functions, proto_name)

    def _disassemble_chunk_txt(self, chunk: LuaChunk, lines: List[str], depth: int, name: str) -> None:
        indent = "  " * depth
        lines.append(f"{indent}function <{name}> (lines {chunk.line_defined}-{chunk.last_line_defined})")
        lines.append(f"{indent}  {chunk.num_params} params, {chunk.max_stack} slots, {chunk.num_upvalues} upvalues")
        lines.append("")

        if chunk.constants:
            lines.append(f"{indent}  Constants ({len(chunk.constants)}):")
            for index, constant in enumerate(chunk.constants):
                lines.append(f"{indent}    [{index}] {constant!r}")
            lines.append("")

        lines.append(f"{indent}  Instructions ({len(chunk.instructions)}):")
        for pc, inst in enumerate(chunk.instructions):
            line = chunk.source_lines[pc][0] if pc < len(chunk.source_lines) else 0
            disasm = self._disassemble_instruction(inst, pc, chunk)
            lines.append(f"{indent}    [{pc}] {line:4} {disasm}")
        lines.append("")

        for index, proto in enumerate(chunk.prototypes):
            proto_name = f"{name}/<{index}>"
            self._disassemble_chunk_txt(proto, lines, depth + 1, proto_name)

    def _disassemble_instruction(self, inst: int, pc: int, chunk: LuaChunk) -> str:
        version = self.version.value
        if version == LUA51:
            return self._disasm_lua51(inst, pc, chunk)
        if version == LUA52:
            return self._disasm_lua52(inst, pc, chunk)
        if version in (LUA53, LUA54):
            return self._disasm_lua53(inst, pc, chunk)
        return f"0x{inst:08x} ; unsupported version"

    def _disassemble_instruction_detailed(self, inst: int, pc: int, chunk: LuaChunk) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        version = self.version.value
        if version == LUA51:
            return self._disasm_lua51_detailed(inst, chunk)
        if version == LUA52:
            return self._disasm_lua52_detailed(inst, chunk)
        if version in (LUA53, LUA54):
            return self._disasm_lua53_detailed(inst, chunk)
        return None

    def _op_register(self, index: int) -> Dict[str, Any]:
        return {"kind": "Register", "id": index}

    def _op_upvalue(self, index: int) -> Dict[str, Any]:
        return {"kind": "Upvalue", "id": index}

    def _op_integer(self, value: int) -> Dict[str, Any]:
        return {"kind": "Integer", "value": value}

    def _op_jump(self, offset: int) -> Dict[str, Any]:
        return {"kind": "Jump", "offset": offset}

    def _op_proto(self, index: int) -> Dict[str, Any]:
        return {"kind": "Proto", "index": index}

    def _op_constant(self, index: int, chunk: LuaChunk) -> Dict[str, Any]:
        const_type, value = self._constant_to_json(chunk.constants[index] if index < len(chunk.constants) else LuaConstant.null())
        return {"kind": "Constant", "index": index, "type": const_type, "value": value}

    def _op_rk(self, value: int, chunk: LuaChunk) -> Dict[str, Any]:
        if value & 0x100:
            return self._op_constant(value & 0xFF, chunk)
        return self._op_register(value)

    def _disasm_lua51(self, inst: int, _pc: int, chunk: LuaChunk) -> str:
        opcode = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = inst >> 14
        sbx = bx - 131071

        def const_str(idx: int) -> str:
            if idx < len(chunk.constants):
                return f"K[{idx}] {chunk.constants[idx]!r}"
            return f"K[{idx}]"

        def rk(x: int) -> str:
            if x & 0x100:
                return const_str(x & 0xFF)
            return f"R[{x}]"

        mapping = {
            0: lambda: f"MOVE      R[{a}] R[{b}]",
            1: lambda: f"LOADK     R[{a}] {const_str(bx)}",
            2: lambda: f"LOADBOOL  R[{a}] {b} {c}",
            3: lambda: f"LOADNIL   R[{a}] {b}",
            4: lambda: f"GETUPVAL  R[{a}] U[{b}]",
            5: lambda: f"GETGLOBAL R[{a}] {const_str(bx)}",
            6: lambda: f"GETTABLE  R[{a}] R[{b}] {rk(c)}",
            7: lambda: f"SETGLOBAL R[{a}] {const_str(bx)}",
            8: lambda: f"SETUPVAL  U[{b}] R[{a}]",
            9: lambda: f"SETTABLE  R[{a}] {rk(b)} {rk(c)}",
            10: lambda: f"NEWTABLE  R[{a}] {b} {c}",
            11: lambda: f"SELF      R[{a}] R[{b}] {rk(c)}",
            12: lambda: f"ADD       R[{a}] {rk(b)} {rk(c)}",
            13: lambda: f"SUB       R[{a}] {rk(b)} {rk(c)}",
            14: lambda: f"MUL       R[{a}] {rk(b)} {rk(c)}",
            15: lambda: f"DIV       R[{a}] {rk(b)} {rk(c)}",
            16: lambda: f"MOD       R[{a}] {rk(b)} {rk(c)}",
            17: lambda: f"POW       R[{a}] {rk(b)} {rk(c)}",
            18: lambda: f"UNM       R[{a}] R[{b}]",
            19: lambda: f"NOT       R[{a}] R[{b}]",
            20: lambda: f"LEN       R[{a}] R[{b}]",
            21: lambda: f"CONCAT    R[{a}] R[{b}] R[{c}]",
            22: lambda: f"JMP       {sbx}",
            23: lambda: f"EQ        {a} {rk(b)} {rk(c)}",
            24: lambda: f"LT        {a} {rk(b)} {rk(c)}",
            25: lambda: f"LE        {a} {rk(b)} {rk(c)}",
            26: lambda: f"TEST      R[{a}] {c}",
            27: lambda: f"TESTSET   R[{a}] R[{b}] {c}",
            28: lambda: f"CALL      R[{a}] nargs={b} nret={c}",
            29: lambda: f"TAILCALL  R[{a}] nargs={b}",
            30: lambda: f"RETURN    R[{a}] n={b}",
            31: lambda: f"FORLOOP   R[{a}] {sbx}",
            32: lambda: f"FORPREP   R[{a}] {sbx}",
            33: lambda: f"TFORLOOP  R[{a}] {c}",
            34: lambda: f"SETLIST   R[{a}] {b} {c}",
            35: lambda: f"CLOSE     R[{a}]",
            36: lambda: f"CLOSURE   R[{a}] P[{bx}]",
            37: lambda: f"VARARG    R[{a}] {b}",
        }
        handler = mapping.get(opcode)
        if handler is not None:
            return handler()
        return f"UNKNOWN   opcode={opcode} A={a} B={b} C={c}"

    def _disasm_lua51_detailed(self, inst: int, chunk: LuaChunk) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        opcode = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = inst >> 14
        sbx = bx - 131071

        r = self._op_register
        u = self._op_upvalue
        i = self._op_integer
        j = self._op_jump
        rk = lambda x: self._op_rk(x, chunk)

        mapping: Dict[int, Tuple[str, List[Dict[str, Any]]]] = {
            0: ("MOVE", [r(a), r(b)]),
            1: ("LOADK", [r(a), self._op_constant(bx, chunk)]),
            2: ("LOADBOOL", [r(a), i(b), i(c)]),
            3: ("LOADNIL", [r(a), i(b)]),
            4: ("GETUPVAL", [r(a), u(b)]),
            5: ("GETGLOBAL", [r(a), self._op_constant(bx, chunk)]),
            6: ("GETTABLE", [r(a), r(b), rk(c)]),
            7: ("SETGLOBAL", [r(a), self._op_constant(bx, chunk)]),
            8: ("SETUPVAL", [u(b), r(a)]),
            9: ("SETTABLE", [r(a), rk(b), rk(c)]),
            10: ("NEWTABLE", [r(a), i(b), i(c)]),
            11: ("SELF", [r(a), r(b), rk(c)]),
            12: ("ADD", [r(a), rk(b), rk(c)]),
            13: ("SUB", [r(a), rk(b), rk(c)]),
            14: ("MUL", [r(a), rk(b), rk(c)]),
            15: ("DIV", [r(a), rk(b), rk(c)]),
            16: ("MOD", [r(a), rk(b), rk(c)]),
            17: ("POW", [r(a), rk(b), rk(c)]),
            18: ("UNM", [r(a), r(b)]),
            19: ("NOT", [r(a), r(b)]),
            20: ("LEN", [r(a), r(b)]),
            21: ("CONCAT", [r(a), r(b), r(c)]),
            22: ("JMP", [j(sbx)]),
            23: ("EQ", [i(a), rk(b), rk(c)]),
            24: ("LT", [i(a), rk(b), rk(c)]),
            25: ("LE", [i(a), rk(b), rk(c)]),
            26: ("TEST", [r(a), i(c)]),
            27: ("TESTSET", [r(a), r(b), i(c)]),
            28: ("CALL", [r(a), i(b), i(c)]),
            29: ("TAILCALL", [r(a), i(b)]),
            30: ("RETURN", [r(a), i(b)]),
            31: ("FORLOOP", [r(a), j(sbx)]),
            32: ("FORPREP", [r(a), j(sbx)]),
            33: ("TFORLOOP", [r(a), i(c)]),
            34: ("SETLIST", [r(a), i(b), i(c)]),
            35: ("CLOSE", [r(a)]),
            36: ("CLOSURE", [r(a), self._op_proto(bx)]),
            37: ("VARARG", [r(a), i(b)]),
        }
        return mapping.get(opcode)

    def _disasm_lua52(self, inst: int, _pc: int, chunk: LuaChunk) -> str:
        opcode = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = inst >> 14
        sbx = bx - 131071
        ax = inst >> 6

        def rk(x: int) -> str:
            if x & 0x100:
                idx = x & 0xFF
                if idx < len(chunk.constants):
                    return f"K[{idx}] {chunk.constants[idx]!r}"
                return f"K[{idx}]"
            return f"R[{x}]"

        if opcode == 0:
            return f"MOVE      R[{a}] R[{b}]"
        if opcode == 1:
            return f"LOADK     R[{a}] {rk(bx | 0x100)}"
        if opcode == 2:
            return f"LOADKX    R[{a}]"
        if opcode == 3:
            return f"LOADBOOL  R[{a}] {b} {c}"
        if opcode == 4:
            return f"LOADNIL   R[{a}] {b}"
        if opcode == 5:
            return f"GETUPVAL  R[{a}] U[{b}]"
        if opcode == 6:
            return f"GETTABUP  R[{a}] U[{b}] {rk(c)}"
        if opcode == 7:
            return f"GETTABLE  R[{a}] R[{b}] {rk(c)}"
        if opcode == 8:
            return f"SETTABUP  U[{a}] {rk(b)} {rk(c)}"
        if opcode == 9:
            return f"SETUPVAL  U[{b}] R[{a}]"
        if opcode == 10:
            return f"SETTABLE  R[{a}] {rk(b)} {rk(c)}"
        if opcode == 11:
            return f"NEWTABLE  R[{a}] {b} {c}"
        if opcode == 12:
            return f"SELF      R[{a}] R[{b}] {rk(c)}"
        if opcode == 13:
            return f"ADD       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 14:
            return f"SUB       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 15:
            return f"MUL       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 16:
            return f"DIV       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 17:
            return f"MOD       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 18:
            return f"POW       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 19:
            return f"UNM       R[{a}] R[{b}]"
        if opcode == 20:
            return f"NOT       R[{a}] R[{b}]"
        if opcode == 21:
            return f"LEN       R[{a}] R[{b}]"
        if opcode == 22:
            return f"CONCAT    R[{a}] R[{b}] R[{c}]"
        if opcode == 23:
            return f"JMP       {sbx}"
        if opcode == 24:
            return f"EQ        {a} {rk(b)} {rk(c)}"
        if opcode == 25:
            return f"LT        {a} {rk(b)} {rk(c)}"
        if opcode == 26:
            return f"LE        {a} {rk(b)} {rk(c)}"
        if opcode == 27:
            return f"TEST      R[{a}] {c}"
        if opcode == 28:
            return f"TESTSET   R[{a}] R[{b}] {c}"
        if opcode == 29:
            return f"CALL      R[{a}] nargs={b} nret={c}"
        if opcode == 30:
            return f"TAILCALL  R[{a}] nargs={b}"
        if opcode == 31:
            return f"RETURN    R[{a}] n={b}"
        if opcode == 32:
            return f"FORLOOP   R[{a}] {sbx}"
        if opcode == 33:
            return f"FORPREP   R[{a}] {sbx}"
        if opcode == 34:
            return f"TFORCALL  R[{a}] {c}"
        if opcode == 35:
            return f"TFORLOOP  R[{a}] {sbx}"
        if opcode == 36:
            return f"SETLIST   R[{a}] {b} {c}"
        if opcode == 37:
            return f"CLOSURE   R[{a}] P[{bx}]"
        if opcode == 38:
            return f"VARARG    R[{a}] {b}"
        if opcode == 39:
            return f"EXTRAARG  {ax}"
        return f"UNKNOWN   opcode={opcode} A={a} B={b} C={c}"

    def _disasm_lua52_detailed(self, inst: int, chunk: LuaChunk) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        opcode = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = inst >> 14
        sbx = bx - 131071
        ax = inst >> 6

        r = self._op_register
        u = self._op_upvalue
        i = self._op_integer
        j = self._op_jump
        rk = lambda x: self._op_rk(x, chunk)

        if opcode == 0:
            return "MOVE", [r(a), r(b)]
        if opcode == 1:
            return "LOADK", [r(a), self._op_constant(bx, chunk)]
        if opcode == 2:
            return "LOADKX", [r(a)]
        if opcode == 3:
            return "LOADBOOL", [r(a), i(b), i(c)]
        if opcode == 4:
            return "LOADNIL", [r(a), i(b)]
        if opcode == 5:
            return "GETUPVAL", [r(a), u(b)]
        if opcode == 6:
            return "GETTABUP", [r(a), u(b), rk(c)]
        if opcode == 7:
            return "GETTABLE", [r(a), r(b), rk(c)]
        if opcode == 8:
            return "SETTABUP", [u(a), rk(b), rk(c)]
        if opcode == 9:
            return "SETUPVAL", [u(b), r(a)]
        if opcode == 10:
            return "SETTABLE", [r(a), rk(b), rk(c)]
        if opcode == 11:
            return "NEWTABLE", [r(a), i(b), i(c)]
        if opcode == 12:
            return "SELF", [r(a), r(b), rk(c)]
        if opcode == 13:
            return "ADD", [r(a), rk(b), rk(c)]
        if opcode == 14:
            return "SUB", [r(a), rk(b), rk(c)]
        if opcode == 15:
            return "MUL", [r(a), rk(b), rk(c)]
        if opcode == 16:
            return "DIV", [r(a), rk(b), rk(c)]
        if opcode == 17:
            return "MOD", [r(a), rk(b), rk(c)]
        if opcode == 18:
            return "POW", [r(a), rk(b), rk(c)]
        if opcode == 19:
            return "UNM", [r(a), r(b)]
        if opcode == 20:
            return "NOT", [r(a), r(b)]
        if opcode == 21:
            return "LEN", [r(a), r(b)]
        if opcode == 22:
            return "CONCAT", [r(a), r(b), r(c)]
        if opcode == 23:
            return "JMP", [i(a), j(sbx)]
        if opcode == 24:
            return "EQ", [i(a), rk(b), rk(c)]
        if opcode == 25:
            return "LT", [i(a), rk(b), rk(c)]
        if opcode == 26:
            return "LE", [i(a), rk(b), rk(c)]
        if opcode == 27:
            return "TEST", [r(a), i(c)]
        if opcode == 28:
            return "TESTSET", [r(a), r(b), i(c)]
        if opcode == 29:
            return "CALL", [r(a), i(b), i(c)]
        if opcode == 30:
            return "TAILCALL", [r(a), i(b)]
        if opcode == 31:
            return "RETURN", [r(a), i(b)]
        if opcode == 32:
            return "FORLOOP", [r(a), j(sbx)]
        if opcode == 33:
            return "FORPREP", [r(a), j(sbx)]
        if opcode == 34:
            return "TFORCALL", [r(a), i(c)]
        if opcode == 35:
            return "TFORLOOP", [r(a), j(sbx)]
        if opcode == 36:
            return "SETLIST", [r(a), i(b), i(c)]
        if opcode == 37:
            return "CLOSURE", [r(a), self._op_proto(bx)]
        if opcode == 38:
            return "VARARG", [r(a), i(b)]
        if opcode == 39:
            return "EXTRAARG", [self._op_integer(ax)]
        return None

    def _disasm_lua53(self, inst: int, _pc: int, chunk: LuaChunk) -> str:
        opcode = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = inst >> 14
        sbx = bx - 131071
        ax = inst >> 6

        def rk(x: int) -> str:
            if x & 0x100:
                idx = x & 0xFF
                if idx < len(chunk.constants):
                    return f"K[{idx}] {chunk.constants[idx]!r}"
                return f"K[{idx}]"
            return f"R[{x}]"

        if opcode == 0:
            return f"MOVE      R[{a}] R[{b}]"
        if opcode == 1:
            return f"LOADK     R[{a}] {rk(bx | 0x100)}"
        if opcode == 2:
            return f"LOADKX    R[{a}]"
        if opcode == 3:
            return f"LOADBOOL  R[{a}] {b} {c}"
        if opcode == 4:
            return f"LOADNIL   R[{a}] {b}"
        if opcode == 5:
            return f"GETUPVAL  R[{a}] U[{b}]"
        if opcode == 6:
            return f"GETTABUP  R[{a}] U[{b}] {rk(c)}"
        if opcode == 7:
            return f"GETTABLE  R[{a}] R[{b}] {rk(c)}"
        if opcode == 8:
            return f"SETTABUP  U[{a}] {rk(b)} {rk(c)}"
        if opcode == 9:
            return f"SETUPVAL  U[{b}] R[{a}]"
        if opcode == 10:
            return f"SETTABLE  R[{a}] {rk(b)} {rk(c)}"
        if opcode == 11:
            return f"NEWTABLE  R[{a}] {b} {c}"
        if opcode == 12:
            return f"SELF      R[{a}] R[{b}] {rk(c)}"
        if opcode == 13:
            return f"ADD       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 14:
            return f"SUB       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 15:
            return f"MUL       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 16:
            return f"MOD       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 17:
            return f"POW       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 18:
            return f"DIV       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 19:
            return f"IDIV      R[{a}] {rk(b)} {rk(c)}"
        if opcode == 20:
            return f"BAND      R[{a}] {rk(b)} {rk(c)}"
        if opcode == 21:
            return f"BOR       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 22:
            return f"BXOR      R[{a}] {rk(b)} {rk(c)}"
        if opcode == 23:
            return f"SHL       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 24:
            return f"SHR       R[{a}] {rk(b)} {rk(c)}"
        if opcode == 25:
            return f"UNM       R[{a}] R[{b}]"
        if opcode == 26:
            return f"BNOT      R[{a}] R[{b}]"
        if opcode == 27:
            return f"NOT       R[{a}] R[{b}]"
        if opcode == 28:
            return f"LEN       R[{a}] R[{b}]"
        if opcode == 29:
            return f"CONCAT    R[{a}] R[{b}] R[{c}]"
        if opcode == 30:
            return f"JMP       {a} (to PC+{sbx})"
        if opcode == 31:
            return f"EQ        {a} {rk(b)} {rk(c)}"
        if opcode == 32:
            return f"LT        {a} {rk(b)} {rk(c)}"
        if opcode == 33:
            return f"LE        {a} {rk(b)} {rk(c)}"
        if opcode == 34:
            return f"TEST      R[{a}] {c}"
        if opcode == 35:
            return f"TESTSET   R[{a}] R[{b}] {c}"
        if opcode == 36:
            return f"CALL      R[{a}] nargs={b} nret={c}"
        if opcode == 37:
            return f"TAILCALL  R[{a}] nargs={b}"
        if opcode == 38:
            return f"RETURN    R[{a}] n={b}"
        if opcode == 39:
            return f"FORLOOP   R[{a}] {sbx}"
        if opcode == 40:
            return f"FORPREP   R[{a}] {sbx}"
        if opcode == 41:
            return f"TFORCALL  R[{a}] {c}"
        if opcode == 42:
            return f"TFORLOOP  R[{a}] {sbx}"
        if opcode == 43:
            return f"SETLIST   R[{a}] {b} {c}"
        if opcode == 44:
            return f"CLOSURE   R[{a}] P[{bx}]"
        if opcode == 45:
            return f"VARARG    R[{a}] {b}"
        if opcode == 46:
            return f"EXTRAARG  {ax}"
        return f"UNKNOWN   opcode={opcode} A={a} B={b} C={c}"

    def _disasm_lua53_detailed(self, inst: int, chunk: LuaChunk) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        opcode = inst & 0x3F
        a = (inst >> 6) & 0xFF
        b = (inst >> 23) & 0x1FF
        c = (inst >> 14) & 0x1FF
        bx = inst >> 14
        sbx = bx - 131071
        ax = inst >> 6

        r = self._op_register
        u = self._op_upvalue
        i = self._op_integer
        j = self._op_jump
        rk = lambda x: self._op_rk(x, chunk)

        if opcode == 0:
            return "MOVE", [r(a), r(b)]
        if opcode == 1:
            return "LOADK", [r(a), self._op_constant(bx, chunk)]
        if opcode == 2:
            return "LOADKX", [r(a)]
        if opcode == 3:
            return "LOADBOOL", [r(a), i(b), i(c)]
        if opcode == 4:
            return "LOADNIL", [r(a), i(b)]
        if opcode == 5:
            return "GETUPVAL", [r(a), u(b)]
        if opcode == 6:
            return "GETTABUP", [r(a), u(b), rk(c)]
        if opcode == 7:
            return "GETTABLE", [r(a), r(b), rk(c)]
        if opcode == 8:
            return "SETTABUP", [u(a), rk(b), rk(c)]
        if opcode == 9:
            return "SETUPVAL", [u(b), r(a)]
        if opcode == 10:
            return "SETTABLE", [r(a), rk(b), rk(c)]
        if opcode == 11:
            return "NEWTABLE", [r(a), i(b), i(c)]
        if opcode == 12:
            return "SELF", [r(a), r(b), rk(c)]
        if opcode == 13:
            return "ADD", [r(a), rk(b), rk(c)]
        if opcode == 14:
            return "SUB", [r(a), rk(b), rk(c)]
        if opcode == 15:
            return "MUL", [r(a), rk(b), rk(c)]
        if opcode == 16:
            return "MOD", [r(a), rk(b), rk(c)]
        if opcode == 17:
            return "POW", [r(a), rk(b), rk(c)]
        if opcode == 18:
            return "DIV", [r(a), rk(b), rk(c)]
        if opcode == 19:
            return "IDIV", [r(a), rk(b), rk(c)]
        if opcode == 20:
            return "BAND", [r(a), rk(b), rk(c)]
        if opcode == 21:
            return "BOR", [r(a), rk(b), rk(c)]
        if opcode == 22:
            return "BXOR", [r(a), rk(b), rk(c)]
        if opcode == 23:
            return "SHL", [r(a), rk(b), rk(c)]
        if opcode == 24:
            return "SHR", [r(a), rk(b), rk(c)]
        if opcode == 25:
            return "UNM", [r(a), r(b)]
        if opcode == 26:
            return "BNOT", [r(a), r(b)]
        if opcode == 27:
            return "NOT", [r(a), r(b)]
        if opcode == 28:
            return "LEN", [r(a), r(b)]
        if opcode == 29:
            return "CONCAT", [r(a), r(b), r(c)]
        if opcode == 30:
            return "JMP", [i(a), j(sbx)]
        if opcode == 31:
            return "EQ", [i(a), rk(b), rk(c)]
        if opcode == 32:
            return "LT", [i(a), rk(b), rk(c)]
        if opcode == 33:
            return "LE", [i(a), rk(b), rk(c)]
        if opcode == 34:
            return "TEST", [r(a), i(c)]
        if opcode == 35:
            return "TESTSET", [r(a), r(b), i(c)]
        if opcode == 36:
            return "CALL", [r(a), i(b), i(c)]
        if opcode == 37:
            return "TAILCALL", [r(a), i(b)]
        if opcode == 38:
            return "RETURN", [r(a), i(b)]
        if opcode == 39:
            return "FORLOOP", [r(a), j(sbx)]
        if opcode == 40:
            return "FORPREP", [r(a), j(sbx)]
        if opcode == 41:
            return "TFORCALL", [r(a), i(c)]
        if opcode == 42:
            return "TFORLOOP", [r(a), j(sbx)]
        if opcode == 43:
            return "SETLIST", [r(a), i(b), i(c)]
        if opcode == 44:
            return "CLOSURE", [r(a), self._op_proto(bx)]
        if opcode == 45:
            return "VARARG", [r(a), i(b)]
        if opcode == 46:
            return "EXTRAARG", [i(ax)]
        return None
