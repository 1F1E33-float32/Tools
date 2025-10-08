from typing import Iterator, List

from .extensions import BinaryReaderHelper


class ScriptInfo:
    def __init__(self):
        self.id: int = 0
        self.source: str = ""


class YSTL:
    MAGIC = 0x4C545359  # 'YSTL'

    def __init__(self):
        self._scripts: List[ScriptInfo] = []

    def __iter__(self) -> Iterator[ScriptInfo]:
        return iter(self._scripts)

    def load(self, file_path: str):
        with open(file_path, "rb") as f:
            self._read(BinaryReaderHelper(f))

    def _read(self, reader: BinaryReaderHelper):
        # Read and validate magic number
        magic = reader.read_int32()
        if magic != self.MAGIC:
            raise ValueError("Not a valid YSTL file.")

        # Read version
        version = reader.read_int32()

        # Read script count
        count = reader.read_int32()

        # Read scripts
        self._scripts = []
        for i in range(count):
            info = ScriptInfo()

            # Read script ID
            info.id = reader.read_int32()

            # Read source path (length-prefixed)
            source_length = reader.read_int32()
            info.source = reader.read_ansi_string(source_length)

            # Read unknown values
            reader.read_int32()
            reader.read_int32()
            reader.read_int32()
            reader.read_int32()

            # Version-specific field
            if version > 462:
                reader.read_int32()

            self._scripts.append(info)
