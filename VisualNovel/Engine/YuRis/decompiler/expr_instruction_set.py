from typing import List, Optional

from .instruction import (
    ArithmeticOperator,
    ArrayAccess,
    ByteLiteral,
    DecimalLiteral,
    Instruction,
    IntLiteral,
    KeywordRef,
    LogicalOperator,
    LongLiteral,
    Nop,
    RawStringLiteral,
    RelationalOperator,
    ShortLiteral,
    UnaryOperator,
    VariableAccess,
    VariableRef,
)
from .yscm import ExpressionInfo


class ExprInstructionSet:
    def __init__(self, script_id: int, instruction: Optional[Instruction] = None):
        self._script_id = script_id
        self._insts: List[Instruction] = []
        self._inst: Optional[Instruction] = instruction

    def get_instructions(self, data: bytes, raw_expr: bool = False):
        offset = 0
        while offset < len(data):
            inst, offset = Instruction.get_instruction(self._script_id, data, offset)
            self._insts.append(inst)

        self.evaluate()

    def evaluate(self):
        stack: List[Instruction] = []

        def build_eval_exception(reason: str, index: int, current: Optional[Instruction], inner: Optional[Exception] = None) -> Exception:
            expr_ctx = ""
            if isinstance(self, AssignExprInstSet):
                kw = self.expr_info.keyword if self.expr_info else None
                rt = self.expr_info.result_type.name if self.expr_info else None
                expr_ctx = f"Expr: Keyword='{kw}', LoadOp='{self.load_op}', ResultType='{rt}'"
            else:
                expr_ctx = "Expr: <no-assign-context>"

            # Dump instructions
            inst_lines = []
            for i, inst in enumerate(self._insts):
                inst_type = type(inst).__name__ if inst else "<null>"
                inst_desc = str(inst) if inst else "<null>"
                inst_lines.append(f"[{i}] {inst_type}: {inst_desc}")
            inst_dump = "\n".join(inst_lines)

            # Dump stack
            if len(stack) == 0:
                stack_dump = "<empty>"
            else:
                stack_dump = " | ".join(f"{type(s).__name__}:{s}" for s in stack)

            current_info = f"{type(current).__name__}:{current}" if current else "<none>"

            msg = f"""EVAL_DIAGNOSTIC
Reason: {reason}
At instruction index: {index}
Current instruction: {current_info}
ScriptId: {self._script_id}
{expr_ctx}
StackCount: {len(stack)}
Stack Snapshot: {stack_dump}
Instruction List:
{inst_dump}"""

            return Exception(msg) if inner is None else Exception(msg + f"\nInner: {inner}")

        try:
            for idx, t in enumerate(self._insts):
                # Arithmetic operators
                if isinstance(t, ArithmeticOperator):
                    if len(stack) < 2:
                        # Special case for assignment expressions
                        if isinstance(self, AssignExprInstSet) and len(stack) == 1:
                            t.right = stack.pop()
                            t.left = KeywordRef(self.expr_info.keyword if self.expr_info else None)
                            stack.append(t)
                            continue
                        raise build_eval_exception("Arithmetic operator requires 2 operands, stack underflow.", idx, t)

                    t.right = stack.pop()
                    t.left = stack.pop()
                    stack.append(t)

                # Relational operators
                elif isinstance(t, RelationalOperator):
                    if len(stack) < 2:
                        if isinstance(self, AssignExprInstSet) and len(stack) == 1:
                            t.right = stack.pop()
                            t.left = KeywordRef(self.expr_info.keyword if self.expr_info else None)
                            stack.append(t)
                            continue
                        raise build_eval_exception("Relational operator requires 2 operands, stack underflow.", idx, t)

                    t.right = stack.pop()
                    t.left = stack.pop()
                    stack.append(t)

                # Logical operators
                elif isinstance(t, LogicalOperator):
                    if len(stack) < 2:
                        if isinstance(self, AssignExprInstSet) and len(stack) == 1:
                            t.right = stack.pop()
                            t.left = KeywordRef(self.expr_info.keyword if self.expr_info else None)
                            stack.append(t)
                            continue
                        raise build_eval_exception("Logical/bitwise operator requires 2 operands, stack underflow.", idx, t)

                    t.right = stack.pop()
                    t.left = stack.pop()
                    stack.append(t)

                # Unary operators
                elif isinstance(t, UnaryOperator):
                    if t.operator == UnaryOperator.Type.NEGATE:
                        if len(stack) < 1:
                            raise build_eval_exception("Negate operator requires 1 operand, stack underflow.", idx, t)

                        top = stack[-1]  # Peek

                        # Negate literals directly
                        if isinstance(top, ByteLiteral):
                            top.value = -top.value
                        elif isinstance(top, ShortLiteral):
                            top.value = -top.value
                        elif isinstance(top, IntLiteral):
                            top.value = -top.value
                        elif isinstance(top, LongLiteral):
                            top.value = -top.value
                        elif isinstance(top, DecimalLiteral):
                            top.value = -top.value
                        elif isinstance(top, ArrayAccess):
                            top.negate = not top.negate
                        elif isinstance(top, VariableAccess):
                            top.negate = not top.negate
                        elif isinstance(top, ArithmeticOperator):
                            top.negate = not top.negate
                        else:
                            raise build_eval_exception(f"Selected object ({top}) does not support negate operator!", idx, t)
                    else:
                        # Other unary operators (ToString, ToNumber)
                        if len(stack) < 1:
                            raise build_eval_exception("Unary operator requires 1 operand, stack underflow.", idx, t)
                        t.operand = stack.pop()
                        stack.append(t)

                # Array access
                elif isinstance(t, ArrayAccess):
                    if len(stack) < 1:
                        raise build_eval_exception("ArrayAccess expects indices and a VariableRef base, but stack is empty.", idx, t)

                    indices = []
                    top = stack.pop()

                    # Collect indices until we find a VariableRef
                    while not isinstance(top, VariableRef):
                        indices.append(top)
                        if len(stack) == 0:
                            raise build_eval_exception("ArrayAccess missing VariableRef before indices are exhausted (unterminated indices).", idx, t)
                        top = stack.pop()

                    indices.reverse()
                    stack.append(ArrayAccess(top, indices))

                # Nop
                elif isinstance(t, Nop):
                    continue

                # Default: push to stack
                else:
                    stack.append(t)

            # Final validation
            if len(stack) != 1:
                raise build_eval_exception(f"Expression did not resolve to a single value (StackCount={len(stack)}).", len(self._insts) - 1, None)

            self._inst = stack[0]

        except Exception as ex:
            raise(build_eval_exception("Evaluation failed.", -1, None, ex))

    def __str__(self) -> str:
        return str(self._inst) if self._inst else ""


class AssignExprInstSet(ExprInstructionSet):
    def __init__(self, script_id: int, expr_info: Optional[ExpressionInfo], load_op: str = "="):
        super().__init__(script_id)
        self.expr_info = expr_info
        self.load_op = load_op

    def get_instructions(self, data: bytes, string_expr: bool = False):
        if string_expr:
            from .extensions import Extensions

            self._insts.append(RawStringLiteral(data.decode(Extensions.get_default_encoding(), errors="replace")))
            self.evaluate()
            return

        super().get_instructions(data)

    def __str__(self) -> str:
        if not self.expr_info or not self.expr_info.keyword:
            return str(self._inst) if self._inst else ""

        # Add parentheses for array variables
        br = ""
        if isinstance(self._inst, VariableAccess) and len(self._inst._var_info.dimensions) > 0:
            br = "()"
        elif isinstance(self._inst, VariableRef) and len(self._inst._var_info.dimensions) > 0:
            br = "()"

        return f"{self.expr_info.keyword}{self.load_op}{self._inst}{br}"
