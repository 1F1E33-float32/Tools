from typing import List

from .extensions import BinaryReaderHelper


class Label:
    def __init__(self):
        self.name: str = ""
        self.name_hash: int = 0
        self.command_index: int = 0
        self.script_id: int = 0
        self.unk2: int = 0
        self.unk3: int = 0


class YSLB:
    MAGIC = 0x424C5359  # 'YSLB'

    def __init__(self):
        self._labels: List[Label] = []

    def load(self, file_path: str):
        with open(file_path, "rb") as f:
            self._read(BinaryReaderHelper(f))

    def _read(self, reader: BinaryReaderHelper):
        # Read and validate magic number
        magic = reader.read_int32()
        if magic != self.MAGIC:
            raise ValueError("Not a valid YSLB file.")

        # Read version (unused)
        _ = reader.read_int32()

        # Read label count
        count = reader.read_int32()

        # Skip 256 integers (hash table or padding)
        for i in range(256):
            reader.read_int32()

        # Read labels
        self._labels = []
        for i in range(count):
            lab = Label()

            # Read label name (length-prefixed)
            name_length = reader.read_byte()
            lab.name = reader.read_ansi_string(name_length)

            # Read label metadata
            lab.name_hash = reader.read_uint32()
            lab.command_index = reader.read_uint32()
            lab.script_id = reader.read_uint16()
            lab.unk2 = reader.read_byte()
            lab.unk3 = reader.read_byte()

            self._labels.append(lab)

    def find(self, script_id: int, command_index: int) -> List[Label]:
        return [label for label in self._labels if label.script_id == script_id and label.command_index == command_index]
