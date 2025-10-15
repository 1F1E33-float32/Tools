from dataclasses import dataclass
from typing import Dict, List, Optional

from .flags import MjoTypeMask


@dataclass
class Opcode:
    value: int
    mnemonic: str
    operator: Optional[str]
    encoding: str
    transition: str
    aliases: List[str]

    @property
    def is_jump(self) -> bool:
        return self.encoding == "j"


class OpcodeRegistry:
    _opcodes: List[Opcode] = []
    _by_value: Dict[int, Opcode] = {}
    _by_mnemonic: Dict[str, Opcode] = {}

    @classmethod
    def _define_opcode(cls, value: int, mnemonic: str, op: Optional[str], encoding: str, transition: str, *aliases: str):
        opcode = Opcode(value, mnemonic, op, encoding, transition, list(aliases))
        cls._opcodes.append(opcode)
        cls._by_value[value] = opcode

        # Register mnemonic and aliases
        cls._by_mnemonic[mnemonic] = opcode
        for alias in aliases:
            cls._by_mnemonic[alias] = opcode

    @classmethod
    def _define_binary_operator(cls, base_value: int, mnemonic: str, op: str, allowed_types: MjoTypeMask, is_comparison: bool, *aliases: str):
        if allowed_types & MjoTypeMask.INT:
            if allowed_types == MjoTypeMask.INT:
                trans = "ii.b" if is_comparison else "ii.i"
                all_aliases = list(aliases) + [a + ".i" for a in aliases] + [mnemonic + ".i"]
                cls._define_opcode(base_value, mnemonic, op, "", trans, *all_aliases)
            else:
                trans = "ii.b" if is_comparison else "ii.i"
                all_aliases = [a + ".i" for a in aliases] + list(aliases) + [mnemonic]
                cls._define_opcode(base_value, mnemonic + ".i", op, "", trans, *all_aliases)

        if allowed_types & MjoTypeMask.FLOAT:
            trans = "nn.b" if is_comparison else "nn.f"
            all_aliases = [a + ".r" for a in aliases]
            cls._define_opcode(base_value + 1, mnemonic + ".r", op, "", trans, *all_aliases)

        if allowed_types & MjoTypeMask.STRING:
            trans = "ss.b" if is_comparison else "ss.s"
            all_aliases = [a + ".s" for a in aliases]
            cls._define_opcode(base_value + 2, mnemonic + ".s", op, "", trans, *all_aliases)

        if allowed_types & MjoTypeMask.INT_ARRAY:
            trans = "II.b" if is_comparison else "-"
            all_aliases = [a + ".iarr" for a in aliases]
            cls._define_opcode(base_value + 3, mnemonic + ".iarr", op, "", trans, *all_aliases)

        if allowed_types & MjoTypeMask.FLOAT_ARRAY:
            trans = "FF.b" if is_comparison else "-"
            all_aliases = [a + ".rarr" for a in aliases]
            cls._define_opcode(base_value + 4, mnemonic + ".rarr", op, "", trans, *all_aliases)

        if allowed_types & MjoTypeMask.STRING_ARRAY:
            trans = "SS.b" if is_comparison else "-"
            all_aliases = [a + ".sarr" for a in aliases]
            cls._define_opcode(base_value + 5, mnemonic + ".sarr", op, "", trans, *all_aliases)

    @classmethod
    def _define_assignment_operator(cls, base_value: int, mnemonic: str, op: str, allowed_types: MjoTypeMask, pop: bool, *aliases: str):
        if allowed_types & MjoTypeMask.INT:
            if allowed_types == MjoTypeMask.INT:
                trans = "i." if pop else "i.i"
                all_aliases = list(aliases) + [a + ".i" for a in aliases] + [mnemonic + ".i"]
                cls._define_opcode(base_value, mnemonic, op, "fho", trans, *all_aliases)
            else:
                trans = "i." if pop else "i.i"
                all_aliases = [a + ".i" for a in aliases] + list(aliases) + [mnemonic]
                cls._define_opcode(base_value, mnemonic + ".i", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.FLOAT:
            trans = "n." if pop else "n.f"
            all_aliases = [a + ".r" for a in aliases]
            cls._define_opcode(base_value + 1, mnemonic + ".r", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.STRING:
            trans = "s." if pop else "s.s"
            all_aliases = [a + ".s" for a in aliases]
            cls._define_opcode(base_value + 2, mnemonic + ".s", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.INT_ARRAY:
            trans = "I." if pop else "I.I"
            all_aliases = [a + ".iarr" for a in aliases]
            cls._define_opcode(base_value + 3, mnemonic + ".iarr", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.FLOAT_ARRAY:
            trans = "F." if pop else "F.F"
            all_aliases = [a + ".rarr" for a in aliases]
            cls._define_opcode(base_value + 4, mnemonic + ".rarr", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.STRING_ARRAY:
            trans = "S." if pop else "S.S"
            all_aliases = [a + ".sarr" for a in aliases]
            cls._define_opcode(base_value + 5, mnemonic + ".sarr", op, "fho", trans, *all_aliases)

    @classmethod
    def _define_array_assignment_operator(cls, base_value: int, mnemonic: str, op: str, allowed_types: MjoTypeMask, pop: bool, *aliases: str):
        if allowed_types & MjoTypeMask.INT:
            if allowed_types == MjoTypeMask.INT:
                trans = "i[i#d]." if pop else "i[i#d].i"
                all_aliases = list(aliases) + [a + ".i" for a in aliases] + [mnemonic + ".i"]
                cls._define_opcode(base_value, mnemonic, op, "fho", trans, *all_aliases)
            else:
                trans = "i[i#d]." if pop else "i[i#d].i"
                all_aliases = [a + ".i" for a in aliases] + list(aliases) + [mnemonic]
                cls._define_opcode(base_value, mnemonic + ".i", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.FLOAT:
            trans = "n[i#d]." if pop else "n[i#d].f"
            all_aliases = [a + ".r" for a in aliases]
            cls._define_opcode(base_value + 1, mnemonic + ".r", op, "fho", trans, *all_aliases)

        if allowed_types & MjoTypeMask.STRING:
            trans = "s[i#d]." if pop else "s[i#d].s"
            all_aliases = [a + ".s" for a in aliases]
            cls._define_opcode(base_value + 2, mnemonic + ".s", op, "fho", trans, *all_aliases)

    @classmethod
    def initialize(cls):
        if cls._opcodes:
            return

        # Binary operators
        cls._define_binary_operator(0x100, "mul", "*", MjoTypeMask.NUMERIC, False)
        cls._define_binary_operator(0x108, "div", "/", MjoTypeMask.NUMERIC, False)
        cls._define_binary_operator(0x110, "rem", "%", MjoTypeMask.INT, False, "mod")
        cls._define_binary_operator(0x118, "add", "+", MjoTypeMask.PRIMITIVE, False)
        cls._define_binary_operator(0x120, "sub", "-", MjoTypeMask.NUMERIC, False)
        cls._define_binary_operator(0x128, "shr", ">>", MjoTypeMask.INT, False)
        cls._define_binary_operator(0x130, "shl", "<<", MjoTypeMask.INT, False)
        cls._define_binary_operator(0x138, "cle", "<=", MjoTypeMask.PRIMITIVE, True)
        cls._define_binary_operator(0x140, "clt", "<", MjoTypeMask.PRIMITIVE, True)
        cls._define_binary_operator(0x148, "cge", ">=", MjoTypeMask.PRIMITIVE, True)
        cls._define_binary_operator(0x150, "cgt", ">", MjoTypeMask.PRIMITIVE, True)
        cls._define_binary_operator(0x158, "ceq", "==", MjoTypeMask.ALL, True)
        cls._define_binary_operator(0x160, "cne", "!=", MjoTypeMask.ALL, True)
        cls._define_binary_operator(0x168, "xor", "^", MjoTypeMask.INT, False)
        cls._define_binary_operator(0x170, "andl", "&&", MjoTypeMask.INT, False)
        cls._define_binary_operator(0x178, "orl", "||", MjoTypeMask.INT, False)
        cls._define_binary_operator(0x180, "and", "&", MjoTypeMask.INT, False)
        cls._define_binary_operator(0x188, "or", "|", MjoTypeMask.INT, False)

        # Unary operators
        cls._define_opcode(0x190, "notl", "!", "", "i.i", "notl.i")
        cls._define_opcode(0x198, "not", "~", "", "i.i", "not.i")
        cls._define_opcode(0x1A0, "neg.i", "-", "", "i.i")
        cls._define_opcode(0x1A1, "neg.r", "-", "", "f.f")
        cls._define_opcode(0x191, "nop.191", None, "", "")
        cls._define_opcode(0x1A8, "nop.1a8", None, "", "")
        cls._define_opcode(0x1A9, "nop.1a9", None, "", "")

        # Assignment operators
        cls._define_assignment_operator(0x1B0, "st", "=", MjoTypeMask.ALL, False)
        cls._define_assignment_operator(0x1B8, "st.mul", "*=", MjoTypeMask.NUMERIC, False)
        cls._define_assignment_operator(0x1C0, "st.div", "/=", MjoTypeMask.NUMERIC, False)
        cls._define_assignment_operator(0x1C8, "st.rem", "%=", MjoTypeMask.INT, False, "st.mod")
        cls._define_assignment_operator(0x1D0, "st.add", "+=", MjoTypeMask.PRIMITIVE, False)
        cls._define_assignment_operator(0x1D8, "st.sub", "-=", MjoTypeMask.NUMERIC, False)
        cls._define_assignment_operator(0x1E0, "st.shl", "<<=", MjoTypeMask.INT, False)
        cls._define_assignment_operator(0x1E8, "st.shr", ">>=", MjoTypeMask.INT, False)
        cls._define_assignment_operator(0x1F0, "st.and", "&=", MjoTypeMask.INT, False)
        cls._define_assignment_operator(0x1F8, "st.xor", "^=", MjoTypeMask.INT, False)
        cls._define_assignment_operator(0x200, "st.or", "|=", MjoTypeMask.INT, False)

        cls._define_assignment_operator(0x210, "stp", "=", MjoTypeMask.ALL, True)
        cls._define_assignment_operator(0x218, "stp.mul", "*=", MjoTypeMask.NUMERIC, True)
        cls._define_assignment_operator(0x220, "stp.div", "/=", MjoTypeMask.NUMERIC, True)
        cls._define_assignment_operator(0x228, "stp.rem", "%=", MjoTypeMask.INT, True, "stp.mod")
        cls._define_assignment_operator(0x230, "stp.add", "+=", MjoTypeMask.PRIMITIVE, True)
        cls._define_assignment_operator(0x238, "stp.sub", "-=", MjoTypeMask.NUMERIC, True)
        cls._define_assignment_operator(0x240, "stp.shl", "<<=", MjoTypeMask.INT, True)
        cls._define_assignment_operator(0x248, "stp.shr", ">>=", MjoTypeMask.INT, True)
        cls._define_assignment_operator(0x250, "stp.and", "&=", MjoTypeMask.INT, True)
        cls._define_assignment_operator(0x258, "stp.xor", "^=", MjoTypeMask.INT, True)
        cls._define_assignment_operator(0x260, "stp.or", "|=", MjoTypeMask.INT, True)

        # Array assignment operators
        cls._define_array_assignment_operator(0x270, "stelem", "=", MjoTypeMask.PRIMITIVE, False)
        cls._define_array_assignment_operator(0x278, "stelem.mul", "*=", MjoTypeMask.NUMERIC, False)
        cls._define_array_assignment_operator(0x280, "stelem.div", "/=", MjoTypeMask.NUMERIC, False)
        cls._define_array_assignment_operator(0x288, "stelem.rem", "%=", MjoTypeMask.INT, False, "stelem.mod")
        cls._define_array_assignment_operator(0x290, "stelem.add", "+=", MjoTypeMask.PRIMITIVE, False)
        cls._define_array_assignment_operator(0x298, "stelem.sub", "-=", MjoTypeMask.NUMERIC, False)
        cls._define_array_assignment_operator(0x2A0, "stelem.shl", "<<=", MjoTypeMask.INT, False)
        cls._define_array_assignment_operator(0x2A8, "stelem.shr", ">>=", MjoTypeMask.INT, False)
        cls._define_array_assignment_operator(0x2B0, "stelem.and", "&=", MjoTypeMask.INT, False)
        cls._define_array_assignment_operator(0x2B8, "stelem.xor", "^=", MjoTypeMask.INT, False)
        cls._define_array_assignment_operator(0x2C0, "stelem.or", "|=", MjoTypeMask.INT, False)

        cls._define_array_assignment_operator(0x2D0, "stelemp", "=", MjoTypeMask.PRIMITIVE, True)
        cls._define_array_assignment_operator(0x2D8, "stelemp.mul", "*=", MjoTypeMask.NUMERIC, True)
        cls._define_array_assignment_operator(0x2E0, "stelemp.div", "/=", MjoTypeMask.NUMERIC, True)
        cls._define_array_assignment_operator(0x2E8, "stelemp.rem", "%=", MjoTypeMask.INT, True, "stelemp.mod")
        cls._define_array_assignment_operator(0x2F0, "stelemp.add", "+=", MjoTypeMask.PRIMITIVE, True)
        cls._define_array_assignment_operator(0x2F8, "stelemp.sub", "-=", MjoTypeMask.NUMERIC, True)
        cls._define_array_assignment_operator(0x300, "stelemp.shl", "<<=", MjoTypeMask.INT, True)
        cls._define_array_assignment_operator(0x308, "stelemp.shr", ">>=", MjoTypeMask.INT, True)
        cls._define_array_assignment_operator(0x310, "stelemp.and", "&=", MjoTypeMask.INT, True)
        cls._define_array_assignment_operator(0x318, "stelemp.xor", "^=", MjoTypeMask.INT, True)
        cls._define_array_assignment_operator(0x320, "stelemp.or", "|=", MjoTypeMask.INT, True)

        # 0x800 range opcodes
        cls._define_opcode(0x800, "ldc.i", None, "i", ".i")
        cls._define_opcode(0x801, "ldstr", None, "s", ".s", "ldc.s")
        cls._define_opcode(0x802, "ld", None, "fho", ".#t", "ldvar")
        cls._define_opcode(0x803, "ldc.r", None, "r", ".f")

        cls._define_opcode(0x80F, "call", None, "h0a", "[*#a].*")
        cls._define_opcode(0x810, "callp", None, "h0a", "[*#a].")

        cls._define_opcode(0x829, "alloca", None, "t", ".[#t]")
        cls._define_opcode(0x82B, "ret", None, "", "[*].", "return")

        cls._define_opcode(0x82C, "br", None, "j", ".", "jmp")
        cls._define_opcode(0x82D, "brtrue", None, "j", "p.", "brinst", "jnz", "jne")
        cls._define_opcode(0x82E, "brfalse", None, "j", "p.", "brnull", "brzero", "jz", "je")

        cls._define_opcode(0x82F, "pop", None, "", "*.")

        cls._define_opcode(0x830, "br.case", None, "j", "p.", "br.v", "jmp.v")
        cls._define_opcode(0x831, "bne.case", None, "j", "p.", "bne.v", "jne.v")
        cls._define_opcode(0x832, "bge.case", None, "j", "p.", "bge.v", "jge.v")
        cls._define_opcode(0x833, "ble.case", None, "j", "p.", "ble.v", "jle.v")
        cls._define_opcode(0x838, "blt.case", None, "j", "p.", "blt.v", "jlt.v")
        cls._define_opcode(0x839, "bgt.case", None, "j", "p.", "bgt.v", "jgt.v")

        cls._define_opcode(0x834, "syscall", None, "ha", "[*#a].*")
        cls._define_opcode(0x835, "syscallp", None, "ha", "[*#a].")

        cls._define_opcode(0x836, "argcheck", None, "t", ".[#t]", "sigchk")

        cls._define_opcode(0x837, "ldelem", None, "fho", "[i#d].#t")

        cls._define_opcode(0x83A, "line", None, "l", ".")

        cls._define_opcode(0x83B, "bsel.1", None, "j", ".")
        cls._define_opcode(0x83C, "bsel.3", None, "j", ".")
        cls._define_opcode(0x83D, "bsel.2", None, "j", ".")

        cls._define_opcode(0x83E, "conv.i", None, "", "f.i")
        cls._define_opcode(0x83F, "conv.r", None, "", "i.f")

        cls._define_opcode(0x840, "text", None, "s", ".")
        cls._define_opcode(0x841, "proc", None, "", ".")
        cls._define_opcode(0x842, "ctrl", None, "s", "[#s].")
        cls._define_opcode(0x843, "bsel.x", None, "j", ".")
        cls._define_opcode(0x844, "bsel.clr", None, "", ".")
        cls._define_opcode(0x845, "bsel.4", None, "j", ".")
        cls._define_opcode(0x846, "bsel.jmp.4", None, "", ".")
        cls._define_opcode(0x847, "bsel.5", None, "j", ".")

        cls._define_opcode(0x850, "switch", None, "c", "i.")

    @classmethod
    def get_by_value(cls, value: int) -> Optional[Opcode]:
        cls.initialize()
        return cls._by_value.get(value)

    @classmethod
    def get_by_mnemonic(cls, mnemonic: str) -> Optional[Opcode]:
        cls.initialize()
        return cls._by_mnemonic.get(mnemonic)


# Initialize on module load
OpcodeRegistry.initialize()
