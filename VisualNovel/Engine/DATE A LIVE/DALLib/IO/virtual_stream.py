from io import SEEK_CUR, SEEK_END, SEEK_SET, IOBase


class VirtualStream(IOBase):
    def __init__(self, internal_stream: IOBase, position: int = None, length: int = None, keep_open: bool = False):
        self._internal_stream = internal_stream
        self._keep_open = keep_open

        if position is None:
            self.new_position = internal_stream.tell()
        else:
            self.new_position = position

        self.new_length = length if length is not None else 0

    def readable(self) -> bool:
        return self._internal_stream.readable()

    def writable(self) -> bool:
        return self._internal_stream.writable()

    def seekable(self) -> bool:
        return self._internal_stream.seekable()

    def tell(self) -> int:
        return self._internal_stream.tell() - self.new_position

    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        if whence == SEEK_SET:
            return self._internal_stream.seek(offset + self.new_position, SEEK_SET)
        elif whence == SEEK_CUR:
            return self._internal_stream.seek(offset, SEEK_CUR)
        elif whence == SEEK_END:
            return self._internal_stream.seek(self.new_position + self.new_length - offset, SEEK_SET)
        else:
            return self._internal_stream.seek(offset, whence)

    def read(self, size: int = -1) -> bytes:
        return self._internal_stream.read(size)

    def write(self, data: bytes) -> int:
        return self._internal_stream.write(data)

    def flush(self):
        self._internal_stream.flush()

    def close(self):
        super().close()
        if not self._keep_open:
            self._internal_stream.close()
