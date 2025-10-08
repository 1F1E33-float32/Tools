from typing import Dict, Optional

from .yscm import YSCM


class CommandIDGenerator:
    _command_names: Dict[int, str] = {}
    _name_to_id: Dict[str, int] = {}

    @staticmethod
    def generate_type(cmd_info: YSCM):
        CommandIDGenerator._command_names = {}
        CommandIDGenerator._name_to_id = {}

        for i, cmd in enumerate(cmd_info.commands_info):
            CommandIDGenerator._command_names[i] = cmd.name
            CommandIDGenerator._name_to_id[cmd.name] = i

    @staticmethod
    def get_id(id_value: int) -> str:
        return CommandIDGenerator._command_names.get(id_value, f"UNKNOWN_{id_value}")

    @staticmethod
    def get_id_by_name(name: str) -> Optional[int]:
        return CommandIDGenerator._name_to_id.get(name)
