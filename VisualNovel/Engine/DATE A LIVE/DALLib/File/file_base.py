import zlib
from io import BytesIO
from typing import BinaryIO

from ..IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter


class FileBase:
    def __init__(self):
        self.use_big_endian = False

    def load(self, path_or_stream, auto_decompress: bool = True, keep_open: bool = False):
        if isinstance(path_or_stream, str):
            # Load from file path
            if keep_open:
                stream = open(path_or_stream, "rb")
                self._load_from_stream(stream, auto_decompress, keep_open)
            else:
                with open(path_or_stream, "rb") as stream:
                    self._load_from_stream(stream, auto_decompress, keep_open)
        else:
            # Load from stream
            self._load_from_stream(path_or_stream, auto_decompress, keep_open)

    def _load_from_stream(self, stream: BinaryIO, auto_decompress: bool = True, keep_open: bool = False):
        reader = ExtendedBinaryReader(stream)

        if auto_decompress:
            # Decompress ZLIB stream
            if reader.peek_signature() == "ZLIB":
                # Skip ZLIB Header
                reader.jump_ahead(14)
                # Decompress stream
                compressed_data = reader.stream.read()
                decompressed_data = zlib.decompress(compressed_data, -zlib.MAX_WBITS)
                reader.set_stream(BytesIO(decompressed_data))
                # Set Endianness of the reader
                reader.set_endian(self.use_big_endian)
                # Parse file
                self.load_from_reader(reader, keep_open)
                return

        # Set Endianness of the reader
        reader.set_endian(self.use_big_endian)
        # Parse File
        self.load_from_reader(reader, keep_open)

    def load_from_reader(self, reader: ExtendedBinaryReader, keep_open: bool = False):
        pass

    def save(self, path_or_stream):
        if isinstance(path_or_stream, str):
            # Save to file path
            with open(path_or_stream, "wb") as stream:
                self._save_to_stream(stream)
        else:
            # Save to stream
            self._save_to_stream(path_or_stream)

    def _save_to_stream(self, stream: BinaryIO):
        self.save_from_writer(ExtendedBinaryWriter(stream))

    def save_from_writer(self, writer: ExtendedBinaryWriter):
        pass
