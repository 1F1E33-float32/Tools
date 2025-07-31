import struct
from typing import List

class YSCM_Header_V5:
    def __init__(self, signature: bytes = b'', version: int = 0, command_count: int = 0, unknown0: int = 0):
        self.signature = signature   # 4 bytes
        self.version = version       # 4 bytes (uint32)
        self.command_count = command_count  # 4 bytes (uint32)
        self.unknown0 = unknown0     # 4 bytes (uint32)

    def __repr__(self):
        return (f"<YSCM_Header_V5 signature={self.signature}, version={self.version}, command_count={self.command_count}, unknown0={self.unknown0}>")

class YSCM_Arg_V5:
    def __init__(self, arg_name: str = '', value0: int = 0, value1: int = 0):
        self.arg_name = arg_name
        self.value0 = value0
        self.value1 = value1

    def __repr__(self):
        return f"<YSCM_Arg_V5 arg_name='{self.arg_name}', value0=0x{self.value0:x}, value1=0x{self.value1:x}>"

    @property
    def arg_size(self) -> int:
        """返回参数在文件中的总字节大小 = (arg_name + '\0') + 1字节 + 1字节 = len + 3."""
        return len(self.arg_name) + 3

    def to_dict(self, arg_id: int):
        return {
            "ID": f"0x{arg_id:x}",
            "Arg": self.arg_name,
            "Value0": f"0x{self.value0:x}",
            "Value1": f"0x{self.value1:x}"
            }

class YSCM_Command_V5:
    def __init__(self, opcode: int = 0, command_name: str = '', args: List[YSCM_Arg_V5] = None):
        self.opcode = opcode
        self.command_name = command_name
        self.args = args or []

    def __repr__(self):
        return (f"<YSCM_Command_V5 opcode=0x{self.opcode:x}, command_name='{self.command_name}', args={self.args}>")

    @property
    def command_size(self) -> int:
        """返回指令在文件中的总字节大小。= (command_name + '\0') + 1字节(参数数量) + 所有参数大小之和."""
        size = len(self.command_name) + 1  # command_name + '\0'
        size += 1                          # arg_count
        for arg in self.args:
            size += arg.arg_size
        return size

    def to_dict(self):
        return {
            "OP": f"0x{self.opcode:x}",
            "Command": self.command_name,
            "Args": [arg.to_dict(i) for i, arg in enumerate(self.args)]
            }

class YSCM_V5:
    def __init__(self):
        self.header = YSCM_Header_V5()
        self.commands: List[YSCM_Command_V5] = []
        self.error_msgs: List[str] = []
        self.unknow_table: bytes = b''

    def load_file(self, filepath: str):
        with open(filepath, 'rb') as f:
            data = f.read()

        header_fmt = "<4sIII"
        header_size = struct.calcsize(header_fmt)
        sig, ver, cmd_count, unk0 = struct.unpack_from(header_fmt, data, 0)

        self.header = YSCM_Header_V5(signature=sig, version=ver, command_count=cmd_count, unknown0=unk0)

        offset = header_size

        # ------------ 2) 解析指令 ------------
        self.commands.clear()
        for i in range(self.header.command_count):
            opcode = i
            cmd_offset = offset

            # 先读 command_name (零结尾字符串)
            cmd_name = _read_cstring(data, cmd_offset)
            cmd_offset += len(cmd_name) + 1

            # 再读参数数量 (1 byte)
            arg_count = data[cmd_offset]
            cmd_offset += 1

            args_list = []
            for _ in range(arg_count):
                arg_offset = cmd_offset
                # 参数名
                arg_name = _read_cstring(data, arg_offset)
                arg_offset += len(arg_name) + 1

                # value0, value1
                value0 = data[arg_offset]
                value1 = data[arg_offset + 1]
                arg_offset += 2

                args_list.append(YSCM_Arg_V5(arg_name, value0, value1))

                cmd_offset = arg_offset

            command_obj = YSCM_Command_V5(opcode, cmd_name, args_list)
            self.commands.append(command_obj)

            offset += command_obj.command_size

        self.error_msgs.clear()
        for _ in range(0x25):  # 0x24+1 次
            msg = _read_cstring(data, offset)
            self.error_msgs.append(msg)
            offset += len(msg) + 1

        self.unknow_table = data[offset: offset + 0x100]
        offset += 0x100

    def to_json_str(self):
        output_dict = {"Commands": [cmd.to_dict() for cmd in self.commands]}
        # output_dict["ErrorMsgs"] = self.error_msgs
        # output_dict["UnknowTableHex"] = self.unknow_table.hex()

        return output_dict

def _read_cstring(data: bytes, start_offset: int) -> str:
    """
    从 data[start_offset] 开始读取以 '\0' 结尾的字符串，返回字符串内容。
    """
    end = start_offset
    while end < len(data) and data[end] != 0:
        end += 1
    return data[start_offset:end].decode('cp932', errors='replace')

def YSCM(ysc_bin_path: str):
    parser = YSCM_V5()
    parser.load_file(ysc_bin_path)

    data = parser.to_json_str()

    for command in data["Commands"]:
        if command.get("Command") == "GOSUB":
            op_value = command.get("OP")
            print(f"Found Command: GOSUB with OP: {op_value}")
            
            for arg in command.get("Args", []):
                if arg.get("Arg") == "PSTR2":
                    id_value = arg.get("ID")
                    print(f"Found Arg: PSTR2 with ID: {id_value}")
                    return int(op_value, 16), int(id_value, 16)