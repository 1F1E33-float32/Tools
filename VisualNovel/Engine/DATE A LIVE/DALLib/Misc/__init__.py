from enum import Enum
from typing import Dict


class DataSizeAttribute:
    def __init__(self, size: int = 4):
        self.size = size


class PropertyNameAttribute:
    def __init__(self, property_name: str):
        self.property_name = property_name


class GameID(Enum):
    NONE = 0
    RINNE_UTOPIA = 1
    ARUSU_INSTALL = 2
    RIO_REINCARNATION = 3


class StringProcessor:
    def __init__(self):
        self.replacement_dictionary: Dict[str, str] = {}

    def load(self, text: str, append: bool = False):
        if not append:
            self.replacement_dictionary.clear()

        for line in text.replace("\r", "").split("\n"):
            parts = line.split("=")
            if len(parts) == 2 and parts[1] not in self.replacement_dictionary:
                self.replacement_dictionary[parts[1]] = parts[0]

    def process(self, text: str) -> str:
        for key, value in self.replacement_dictionary.items():
            text = text.replace(key, value)
        return text

    def process_reverse(self, text: str) -> str:
        for key, value in self.replacement_dictionary.items():
            text = text.replace(value, key)
        return text


__all__ = ["DataSizeAttribute", "PropertyNameAttribute", "GameID", "StringProcessor"]
