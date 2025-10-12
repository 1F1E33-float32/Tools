"""
BGI Script Decompiler - Stack-based VM to high-level code converter
"""

import struct
import os
import argparse
from typing import List, Dict, Tuple, Any, Optional


class StackValue:
    """Represents a value on the VM stack"""
    pass


class Constant(StackValue):
    """Integer constant"""
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return str(self.value)


class String(StackValue):
    """String constant"""
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f'"{self.value}"'


class Variable(StackValue):
    """Variable reference"""
    def __init__(self, index: int):
        self.index = index

    def __repr__(self):
        return f"var_{self.index}"


class BinaryOp(StackValue):
    """Binary operation result"""
    def __init__(self, op: str, left: StackValue, right: StackValue):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        # Add parentheses for clarity
        return f"({self.left} {self.op} {self.right})"


class UnaryOp(StackValue):
    """Unary operation result"""
    def __init__(self, op: str, operand: StackValue):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"{self.op}({self.operand})"


class FunctionCall(StackValue):
    """Function call result"""
    def __init__(self, name: str, args: List[StackValue]):
        self.name = name
        self.args = args

    def __repr__(self):
        args_str = ", ".join(str(arg) for arg in reversed(self.args))
        return f"{self.name}({args_str})"


class BGIDecompiler:
    """Decompiles BGI bytecode to readable code"""

    def __init__(self):
        self.stack: List[StackValue] = []
        self.instructions: List[Tuple[int, str, Any]] = []
        self.output: List[str] = []
        self.defines: Dict[int, str] = {}
        self.pending_nargs: Optional[int] = None

        # Binary operators mapping
        self.binary_ops = {
            0x020: '+',   # add
            0x021: '-',   # sub
            0x022: '*',   # mul
            0x023: '/',   # div
            0x024: '%',   # mod
            0x025: '&',   # and
            0x026: '|',   # or
            0x027: '^',   # xor
            0x029: '<<',  # shl
            0x02A: '>>',  # shr
            0x02B: '>>',  # sar (arithmetic shift)
            0x030: '==',  # eq
            0x031: '!=',  # neq
            0x032: '<=',  # leq
            0x033: '>=',  # geq
            0x034: '<',   # lt
            0x035: '>',   # gt
            0x038: '&&',  # bool_and
            0x039: '||',  # bool_or
        }

        # Unary operators mapping
        self.unary_ops = {
            0x028: '~',   # not (bitwise)
            0x03A: '!',   # bool_zero (logical not)
        }

    def push(self, value: StackValue):
        """Push value onto stack"""
        self.stack.append(value)

    def pop(self) -> StackValue:
        """Pop value from stack"""
        if not self.stack:
            raise Exception("Stack underflow")
        return self.stack.pop()

    def pop_n(self, n: int) -> List[StackValue]:
        """Pop n values from stack"""
        if len(self.stack) < n:
            raise Exception(f"Stack underflow: need {n}, have {len(self.stack)}")
        args = []
        for _ in range(n):
            args.append(self.pop())
        return args

    def escape_string(self, text: str) -> str:
        """Escape special characters in string"""
        text = text.replace("\\", "\\\\")
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "\\r")
        text = text.replace("\t", "\\t")
        text = text.replace('"', '\\"')
        return text

    def process_instruction(self, addr: int, opcode: int, args: Any):
        """Process a single instruction"""

        # Stack push operations
        if opcode == 0x000:  # push_dword
            self.push(Constant(args))

        elif opcode == 0x003:  # push_string
            self.push(String(self.escape_string(args)))

        elif opcode == 0x008:  # load (variable)
            self.push(Variable(args))

        # Binary operations
        elif opcode in self.binary_ops:
            right = self.pop()
            left = self.pop()
            op_symbol = self.binary_ops[opcode]
            self.push(BinaryOp(op_symbol, left, right))

        # Unary operations
        elif opcode in self.unary_ops:
            operand = self.pop()
            op_symbol = self.unary_ops[opcode]
            self.push(UnaryOp(op_symbol, operand))

        # nargs - marks number of arguments for next function call
        elif opcode == 0x03F:
            self.pending_nargs = args

        # Function calls (0x100-0x3FF)
        elif 0x100 <= opcode < 0x400:
            # Determine function namespace
            if 0x100 <= opcode < 0x140:
                namespace = "sys_"
            elif 0x140 <= opcode < 0x160:
                namespace = "msg_"
            elif 0x160 <= opcode < 0x180:
                namespace = "slct"
            elif 0x180 <= opcode < 0x200:
                namespace = "snd_"
            elif 0x200 <= opcode < 0x400:
                namespace = "grp_"
            else:
                namespace = ""

            func_name = f"{namespace}::f_{opcode:03x}" if namespace else f"f_{opcode:03x}"

            # Get arguments from stack
            if self.pending_nargs is not None:
                nargs = self.pending_nargs
                self.pending_nargs = None
            else:
                # If no nargs specified, assume function consumes all stack
                nargs = len(self.stack)

            args_list = self.pop_n(nargs)

            # Check if this is a statement or expression
            # If stack is empty after pop, it's a statement
            # Otherwise, push result back (it's used in an expression)
            if len(self.stack) == 0:
                # Statement: output directly
                call = FunctionCall(func_name, args_list)
                self.output.append(f"\t{call};")
            else:
                # Expression: push result back to stack
                self.push(FunctionCall(func_name, args_list))

        # Other function calls (0x00-0xFF)
        elif opcode < 0x100 and opcode not in [0x000, 0x003, 0x008, 0x03F] and opcode not in self.binary_ops and opcode not in self.unary_ops:
            func_name = f"f_{opcode:03x}"

            if self.pending_nargs is not None:
                nargs = self.pending_nargs
                self.pending_nargs = None
            else:
                nargs = len(self.stack)

            args_list = self.pop_n(nargs)

            if len(self.stack) == 0:
                call = FunctionCall(func_name, args_list)
                self.output.append(f"\t{call};")
            else:
                self.push(FunctionCall(func_name, args_list))

        # Line directive - output as comment
        elif opcode == 0x07F:
            filename, lineno = args
            self.output.append(f'\t// line("{filename}", {lineno})')

    def decompile_block(self, instructions: List[Tuple[int, int, Any]], defines: Dict[int, str]) -> List[str]:
        """Decompile a block of instructions"""
        self.stack = []
        self.output = []
        self.defines = defines
        self.pending_nargs = None

        for addr, opcode, args in instructions:
            # Check if this address has a label
            if addr in defines:
                self.output.append(f"\n{defines[addr]}:")

            self.process_instruction(addr, opcode, args)

        return self.output


def test_decompiler():
    """Test the decompiler with example instructions"""
    decompiler = BGIDecompiler()

    # Example 1: snd_::f_190(0, 110, "lse0140", 0)
    print("Example 1:")
    instructions1 = [
        (0x000, 0x07F, ("test.bsb", 60)),  # line directive
        (0x008, 0x000, 0),                  # push_dword(0)
        (0x00C, 0x003, "lse0140"),          # push_string("lse0140")
        (0x010, 0x000, 110),                # push_dword(110)
        (0x014, 0x000, 0),                  # push_dword(0)
        (0x018, 0x03F, 4),                  # nargs(4)
        (0x01C, 0x190, None),               # snd_::f_190()
    ]
    result1 = decompiler.decompile_block(instructions1, {})
    for line in result1:
        print(line)

    # Example 2: msg_::f_140(...)
    print("\n\nExample 2:")
    instructions2 = [
        (0x000, 0x07F, ("test.bsb", 39)),
        (0x008, 0x07B, (0x12345678, 1, 20525)),  # f_07b (special)
        (0x00C, 0x000, 1),
        (0x010, 0x000, 1),
        (0x014, 0x000, 0),
        (0x018, 0x003, "浩一"),
        (0x01C, 0x003, "（……さて、知美は何処にいるかな）"),
        (0x020, 0x140, None),
    ]
    result2 = decompiler.decompile_block(instructions2, {})
    for line in result2:
        print(line)

    # Example 3: f_0e0(120, f_0e1(120) + 1)
    print("\n\nExample 3:")
    instructions3 = [
        (0x000, 0x07F, ("test.bsb", 85)),
        (0x004, 0x000, 120),                # push_dword(120)
        (0x008, 0x000, 120),                # push_dword(120)
        (0x00C, 0x03F, 1),                  # nargs(1)
        (0x010, 0x0E1, None),               # f_0e1()
        (0x014, 0x000, 1),                  # push_dword(1)
        (0x018, 0x020, None),               # add()
        (0x01C, 0x03F, 2),                  # nargs(2)
        (0x020, 0x0E0, None),               # f_0e0()
    ]
    result3 = decompiler.decompile_block(instructions3, {0x464: "L00464"})
    for line in result3:
        print(line)


if __name__ == "__main__":
    test_decompiler()
