from typing import Dict


class StringProcessor:
    def __init__(self):
        self.replacement_dictionary: Dict[str, str] = {}

    def load(self, text: str, append: bool = False) -> None:
        if not append:
            self.replacement_dictionary.clear()

        # Process each line
        for line in text.replace("\r", "").split("\n"):
            parts = line.split("=")
            if len(parts) == 2:
                # Format is value=key, so we store as key -> value
                key = parts[1]
                value = parts[0]
                if key not in self.replacement_dictionary:
                    self.replacement_dictionary[key] = value

    def process(self, text: str) -> str:
        for key, value in self.replacement_dictionary.items():
            text = text.replace(key, value)
        return text

    def process_reverse(self, text: str) -> str:
        for key, value in self.replacement_dictionary.items():
            text = text.replace(value, key)
        return text


__all__ = ["StringProcessor"]
