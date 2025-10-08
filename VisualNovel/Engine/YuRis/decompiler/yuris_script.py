import json
from io import StringIO
from pathlib import Path
from typing import List, Optional

from .command_id_generator import CommandIDGenerator
from .extensions import Extensions
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
    StringLiteral,
    UnaryOperator,
    VariableAccess,
    VariableRef,
)
from .yscm import YSCM
from .yslb import YSLB
from .ystb import YSTB
from .ystl import YSTL
from .ysvr import YSVR


class InstructionJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Instruction):
            return self._serialize_instruction(obj)
        return super().default(obj)

    def _serialize_instruction(self, inst: Optional[Instruction]) -> Optional[dict]:
        if inst is None:
            return None

        inst_type = type(inst).__name__

        # Binary operators
        if isinstance(inst, (ArithmeticOperator, RelationalOperator, LogicalOperator)):
            return {"type": inst_type, "operator": inst.operator.name, "left": self._serialize_instruction(inst.left), "right": self._serialize_instruction(inst.right), "negate": getattr(inst, "negate", False)}

        # Unary operators
        if isinstance(inst, UnaryOperator):
            return {"type": inst_type, "operator": inst.operator.name, "operand": self._serialize_instruction(inst.operand)}

        # Array access
        if isinstance(inst, ArrayAccess):
            return {"type": inst_type, "variable": self._serialize_instruction(inst.variable), "indices": [self._serialize_instruction(idx) for idx in inst.indices], "negate": inst.negate}

        # Literals
        if isinstance(inst, (ByteLiteral, ShortLiteral, IntLiteral, LongLiteral, DecimalLiteral)):
            return {"type": inst_type, "value": inst.value}

        if isinstance(inst, (StringLiteral, RawStringLiteral)):
            return {"type": inst_type, "value": inst.value}

        # Variable access
        if isinstance(inst, VariableAccess):
            return {"type": inst_type, "mode": chr(inst.mode), "varId": inst.var_id, "varName": YSVR.get_decompiled_var_name(inst._var_info), "negate": inst.negate}

        # Variable reference
        if isinstance(inst, VariableRef):
            return {"type": inst_type, "varId": inst.var_id, "varName": YSVR.get_decompiled_var_name(inst._var_info)}

        # Keyword reference
        if isinstance(inst, KeywordRef):
            return {"type": inst_type, "name": inst.name}

        # Nop
        if isinstance(inst, Nop):
            return {"type": inst_type}

        # Default fallback
        return {"type": inst_type, "text": str(inst)}


class YuRisScript:
    def __init__(self):
        self._dir_path: str = ""
        self._yscm: Optional[YSCM] = None
        self._yslb: Optional[YSLB] = None
        self._ystl: Optional[YSTL] = None
        self._ybn_key: Optional[bytes] = None

    def init(self, dir_path: str, ybn_key: Optional[bytes]):
        self._dir_path = dir_path

        # Load command metadata
        self._yscm = YSCM()
        self._yscm.load(str(Path(dir_path) / "ysc.ybn"))

        # Generate command ID mappings
        CommandIDGenerator.generate_type(self._yscm)

        # Load label data
        self._yslb = YSLB()
        self._yslb.load(str(Path(dir_path) / "ysl.ybn"))

        # Load script list
        self._ystl = YSTL()
        self._ystl.load(str(Path(dir_path) / "yst_list.ybn"))

        # Load variable data
        YSVR.load(str(Path(dir_path) / "ysv.ybn"))

        self._ybn_key = ybn_key

    def decompile(self, script_index: int, output_stream: Optional[StringIO] = None) -> bool:
        print(f"Decompiling yst{script_index:05d}.ybn ...", end="")

        ystb = YSTB(self._yscm, self._yslb)
        file_path = str(Path(self._dir_path) / f"yst{script_index:05d}.ybn")

        if not ystb.load(file_path, script_index, self._ybn_key):
            return False

        if output_stream is None:
            output_stream = StringIO()

        commands = ystb.commands
        nest_depth = 0

        for i, cmd in enumerate(commands):
            # Find labels for this command
            labels = self._yslb.find(script_index, i)

            if labels:
                for label in labels:
                    output_stream.write(f"#={label.name}\n")

            # Handle indentation based on command type
            cmd_name = cmd.id

            if cmd_name in ("IF", "LOOP"):
                output_stream.write("".ljust(nest_depth * 4))
                nest_depth += 1
            elif cmd_name == "ELSE":
                output_stream.write("".ljust(max(0, nest_depth - 1) * 4))
            elif cmd_name in ("IFEND", "LOOPEND"):
                nest_depth = max(0, nest_depth - 1)
                output_stream.write("".ljust(nest_depth * 4))
            else:
                output_stream.write("".ljust(nest_depth * 4))

            output_stream.write(str(cmd) + "\n")

        return True

    def decompile_project(self):
        source_paths = []

        for script in self._ystl:
            source_path = Path(self._dir_path) / script.source
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_paths.append(str(source_path))

            text_writer = StringIO()
            if self.decompile(script.id, text_writer):
                data = text_writer.getvalue()

                # Handle empty files
                if data.startswith("END[]") and len(data) < 8:
                    source_path.write_text("//Empty file.", encoding=Extensions.get_default_encoding())
                else:
                    # Remove last 8 characters (END[] + newline)
                    if len(data) >= 8:
                        data = data[:-8]
                    source_path.write_bytes(data.encode(Extensions.get_default_encoding(), errors="replace"))

                print(f" -> {source_path}")
            else:
                print(" -> Failed. No such file.")

        # Write global variables
        longest_common_path = self._find_common_path(source_paths)
        global_path = Path(longest_common_path) / "global.txt"

        global_var_writer = StringIO()
        YSVR.write_global_var_decl(global_var_writer)
        global_path.write_bytes(global_var_writer.getvalue().encode(Extensions.get_default_encoding(), errors="replace"))

    def decompile_project_json(self):
        scripts = []

        for script in self._ystl:
            source_path = Path(self._dir_path) / script.source
            source_path.parent.mkdir(parents=True, exist_ok=True)
            scripts.append((script.id, str(source_path)))

            model = self._build_script_model(script.id, script.source)
            if model is None:
                print(f"Decompiling yst{script.id:05d}.ybn ... -> Failed. No such file.")
                continue

            json_path = source_path.with_suffix(".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(model, f, indent=2, ensure_ascii=False, cls=InstructionJSONEncoder)

            print(f"Decompiling yst{script.id:05d}.ybn ... -> {json_path}")

        # Write global variables JSON
        longest_common_path = self._find_common_path([s[1] for s in scripts])
        globals_json_path = Path(longest_common_path) / "global.json"

        globals_model = self._build_globals_model()
        with open(globals_json_path, "w", encoding="utf-8") as f:
            json.dump(globals_model, f, indent=2, ensure_ascii=False, cls=InstructionJSONEncoder)

    def _build_script_model(self, script_index: int, source: str) -> Optional[dict]:
        ystb = YSTB(self._yscm, self._yslb)
        file_path = str(Path(self._dir_path) / f"yst{script_index:05d}.ybn")

        if not ystb.load(file_path, script_index, self._ybn_key):
            return None

        commands = ystb.commands
        items = []
        nest_depth = 0

        for i, cmd in enumerate(commands):
            cmd_name = cmd.id
            labels = self._yslb.find(script_index, i) or []

            # Calculate nesting level
            if cmd_name in ("IF", "LOOP"):
                line_nest_before = nest_depth
                nest_depth += 1
            elif cmd_name == "ELSE":
                line_nest_before = max(0, nest_depth - 1)
            elif cmd_name in ("IFEND", "LOOPEND"):
                nest_depth = max(0, nest_depth - 1)
                line_nest_before = nest_depth
            else:
                line_nest_before = nest_depth

            # Build expressions
            exprs = []
            if cmd.expressions:
                for e in cmd.expressions:
                    expr_data = {
                        "id": e.id,
                        "flag": e.flag,
                        "argLoadFn": e.arg_load_fn,
                        "argLoadOp": e.arg_load_op,
                        "loadOp": e.get_load_op(),
                        "instructionSize": e.instruction_size,
                        "instructionOffset": e.instruction_offset,
                        "text": str(e.expr_insts) if e.expr_insts else None,
                        "ast": e.expr_insts._inst if e.expr_insts else None,
                    }
                    exprs.append(expr_data)

            # Get command ID as integer
            cmd_id_numeric = None
            for idx, cmd_info in enumerate(self._yscm.commands_info):
                if cmd_info.name == cmd_name:
                    cmd_id_numeric = idx
                    break

            items.append(
                {
                    "index": i,
                    "id": cmd_name,
                    "idNumeric": cmd_id_numeric,
                    "exprCount": cmd.expr_count,
                    "labelId": cmd.label_id,
                    "lineNumber": cmd.line_number,
                    "nest": line_nest_before,
                    "labels": [label.name for label in labels],
                    "expressions": exprs,
                }
            )

        return {"scriptId": script_index, "source": source, "commands": items}

    def _build_globals_model(self) -> List[dict]:
        result = []
        for variable in YSVR.enumerate_variables():
            result.append(
                {
                    "scope": variable.scope.name,
                    "scriptIndex": variable.script_index,
                    "variableId": variable.variable_id,
                    "type": variable.type,
                    "name": YSVR.get_decompiled_var_name(variable),
                    "dimensions": variable.dimensions or [],
                    "value": variable.value,
                }
            )
        return result

    def _find_common_path(self, paths: List[str]) -> str:
        if not paths:
            return self._dir_path

        # Split paths into components
        path_components = [Path(p).parts for p in paths]

        # Find common prefix
        common = []
        if path_components:
            for components in zip(*path_components):
                if len(set(c.lower() for c in components)) == 1:
                    common.append(components[0])
                else:
                    break

        if common:
            return str(Path(*common))
        return self._dir_path
