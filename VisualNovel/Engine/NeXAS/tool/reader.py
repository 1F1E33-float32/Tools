import io
import struct
from typing import Any, Dict, List

from ruamel.yaml.scalarstring import SingleQuotedScalarString

from .constants import LENGTH_PREFIXED, NULL_TERMINATED
from .script_data import GlobalScript, Instruction, Script


class Reader:
    def __init__(self, config):
        self.data = io.BytesIO()
        self.config = config
        if self.config["string_format"] == NULL_TERMINATED:
            self.read_string = self._read_null_terminated_string
        elif self.config["string_format"] == LENGTH_PREFIXED:
            self.read_string = self._read_length_prefixed_string
        else:
            raise ValueError("Undefined string format")

    def _read_i32(self):
        return struct.unpack("<i", self.data.read(4))[0]

    def _read_null_terminated_string(self):
        bstr = b""
        c = self.data.read(1)
        while c != b"\x00":
            bstr += c
            c = self.data.read(1)
        return bstr.decode(self.config["encoding"])

    def _read_length_prefixed_string(self):
        length = self._read_i32()
        string = self.data.read(length).decode(self.config["encoding"])
        return string[:-1]  # Remove null byte


class ScriptReader(Reader):
    def __init__(self, config):
        super().__init__(config)

    def _read_version(self) -> None:
        if self.config["version_format"] == LENGTH_PREFIXED:
            self.data.seek(13, 1)  # 09 00 00 00 56 45 52 2D 31 2E 30 30 00 <= length + VER-1.00\0 + unknown unchanging data
            unk_count = self._read_i32()
            self.data.seek(unk_count * 4, 1)
        elif self.config["version_format"] == NULL_TERMINATED:
            self.data.seek(9, 1)  # 56 45 52 2D 31 2E 30 30 00 <= VER-1.00\0 + unknown unchanging data
            unk_count = self._read_i32()
            self.data.seek(unk_count * 4, 1)

    def _read_instructions(self) -> List[Instruction]:
        code_count = self._read_i32()
        return [Instruction(*struct.unpack("<ii", self.data.read(8))) for i in range(code_count)]

    def _read_string_list(self) -> Dict[int, str]:
        length = self._read_i32()
        result = {}
        for i in range(length):
            raw = self.read_string()
            result[i] = SingleQuotedScalarString(raw)
        return result

    def _read_banks_params(self) -> Dict[int, Any]:
        bank_count = self._read_i32()
        banks = {}
        for _ in range(bank_count):
            bank_no = self._read_i32()
            params = [{"int_var_index": self._read_i32()} for _ in range(8)]
            for i in range(8):
                params[i]["default_value"] = self._read_i32()
            banks[bank_no] = params
        return banks

    def _read_functions(self) -> Dict[int, Any]:
        functions = {}
        while True:
            key = self.data.read(4)
            if not key:
                break
            key = struct.unpack("<i", key)[0]
            cnt = self._read_i32()
            self.data.seek(cnt * 8, 1)
            functions[key] = {"code": self._read_instructions(), "string_table": self._read_string_list(), "int_var_names": self._read_string_list(), "string_var_names": self._read_string_list()}
            cnt = self._read_i32()
            self.data.seek(cnt * 68, 1)
        return functions

    def read_script_from_file(self, input: str) -> Script:

        with open(input, "rb") as file:
            self.data = io.BytesIO(file.read())

        self._read_version()
        init_code = self._read_instructions()
        code = self._read_instructions()
        string_table = self._read_string_list()
        int_var_names = self._read_string_list()
        string_var_names = self._read_string_list()
        banks_params = self._read_banks_params()
        functions = self._read_functions()

        return Script(init_code, code, string_table, int_var_names, string_var_names, banks_params, functions)

    def read_global_script_from_file(self, input: str) -> GlobalScript:
        with open(input, "rb") as file:
            self.data = io.BytesIO(file.read())

        int_var_names = self._read_string_list()
        string_var_names = self._read_string_list()
        string_table = self._read_string_list()
        code = self._read_instructions()

        return GlobalScript(int_var_names, string_var_names, string_table, code)
