import struct
from io import BytesIO
from typing import BinaryIO, Dict, Optional


class StreamBlock:
    def __init__(self, position: int, length: int):
        self.position = position
        self.length = length


class ExtendedBinaryReader:
    def __init__(self, stream: BinaryIO, is_big_endian: bool = False):
        self.stream = stream
        self.is_big_endian = is_big_endian
        self.offset = 0

    @property
    def base_stream(self) -> BinaryIO:
        return self.stream

    def set_stream(self, stream: BinaryIO):
        self.stream = stream

    def set_endian(self, is_big_endian: bool):
        self.is_big_endian = is_big_endian

    def get_length(self) -> int:
        current = self.stream.tell()
        self.stream.seek(0, 2)  # Seek to end
        length = self.stream.tell()
        self.stream.seek(current)
        return length

    def get_position(self) -> int:
        return self.stream.tell()

    def jump_to(self, position: int, absolute: bool = True):
        if absolute:
            self.stream.seek(position)
        else:
            self.stream.seek(position + self.offset)

    def jump_ahead(self, amount: int = 1):
        self.stream.seek(amount, 1)

    def jump_behind(self, amount: int = 1):
        self.stream.seek(-amount, 1)

    def fix_padding(self, amount: int = 4):
        if amount < 1:
            return
        jump_amount = 0
        while (self.stream.tell() + jump_amount) % amount != 0:
            jump_amount += 1
        self.jump_ahead(jump_amount)

    def read_signature(self, length: int = 4) -> str:
        return self.read_bytes(length).decode("ascii", errors="ignore")

    def peek_signature(self, length: int = 4) -> str:
        result = self.read_signature(length)
        self.jump_behind(length)
        return result

    def read_trimmed_string(self, length: int = 4) -> str:
        return self.read_signature(length).rstrip("\x00")

    def read_null_terminated_string(self) -> str:
        chars = []
        while True:
            char = self.stream.read(1)
            if not char or char == b"\x00":
                break
            chars.append(char)
        return b"".join(chars).decode("utf-8", errors="ignore")

    def read_string_elsewhere(self, position: int = 0, absolute: bool = True) -> Optional[str]:
        old_pos = self.stream.tell()
        use_pointer = position == 0
        try:
            if use_pointer:
                target = self.read_int32()
                self.jump_to(target, absolute)
            else:
                self.jump_to(position, absolute)

            if self.stream.tell() == (0 if absolute else self.offset):
                if use_pointer:
                    self.jump_to(old_pos + 4)
                else:
                    self.jump_to(old_pos)
                return None

            if self.offset > self.stream.tell():
                self.offset = self.stream.tell()

            s = self.read_null_terminated_string()

            if use_pointer:
                self.jump_to(old_pos + 4)
            else:
                self.jump_to(old_pos)

            return s
        except Exception:
            self.jump_to(old_pos)
            return ""

    def read_null_terminated_string_pointer(self) -> Optional[str]:
        old_pos = self.stream.tell()
        try:
            self.jump_to(self.read_int32())
            self.jump_to(self.read_int32())
            if self.offset > self.stream.tell():
                self.offset = self.stream.tell()
            s = self.read_null_terminated_string()
            self.jump_to(old_pos + 4)
            return s
        except Exception:
            self.jump_to(old_pos + 4)
            return ""

    def check_dal_signature(self, expected: str) -> int:
        sig = self.read_signature(len(expected))
        if sig != expected:
            return 0

        # Calculate size of padding
        padding = 0
        while True:
            byte = self.read_byte()
            if byte != 0x20:  # Space character
                if len(expected) + padding >= 0x14:
                    self.jump_behind((len(expected) + padding) - 0x14 + 1)
                elif len(expected) + padding >= 0x0C:
                    self.jump_behind((len(expected) + padding) - 0x0C + 1)
                elif len(expected) + padding >= 0x08:
                    self.jump_behind((len(expected) + padding) - 0x08 + 1)
                break
            padding += 1

        return len(expected) + padding

    def read_dal_signature(self, expected: str) -> str:
        sig = self.read_signature(len(expected))
        if sig != expected:
            return sig

        # Calculate size of padding
        padding = 0
        while True:
            byte = self.read_byte()
            if byte != 0x20:  # Space character
                if len(expected) + padding >= 0x14:
                    self.jump_behind((len(expected) + padding) - 0x14 + 1)
                elif len(expected) + padding >= 0x0C:
                    self.jump_behind((len(expected) + padding) - 0x0C + 1)
                elif len(expected) + padding >= 0x08:
                    self.jump_behind((len(expected) + padding) - 0x08 + 1)
                break
            padding += 1

        return sig + " " * padding

    # Basic type reading methods
    def read_byte(self) -> int:
        return struct.unpack("B", self.stream.read(1))[0]

    def read_sbyte(self) -> int:
        return struct.unpack("b", self.stream.read(1))[0]

    def read_bool(self) -> bool:
        return self.read_byte() != 0

    def read_int16(self) -> int:
        """Read a 16-bit signed integer"""
        fmt = ">h" if self.is_big_endian else "<h"
        return struct.unpack(fmt, self.stream.read(2))[0]

    def read_uint16(self) -> int:
        """Read a 16-bit unsigned integer"""
        fmt = ">H" if self.is_big_endian else "<H"
        return struct.unpack(fmt, self.stream.read(2))[0]

    def read_int32(self) -> int:
        """Read a 32-bit signed integer"""
        fmt = ">i" if self.is_big_endian else "<i"
        return struct.unpack(fmt, self.stream.read(4))[0]

    def read_uint32(self) -> int:
        """Read a 32-bit unsigned integer"""
        fmt = ">I" if self.is_big_endian else "<I"
        return struct.unpack(fmt, self.stream.read(4))[0]

    def read_int64(self) -> int:
        """Read a 64-bit signed integer"""
        fmt = ">q" if self.is_big_endian else "<q"
        return struct.unpack(fmt, self.stream.read(8))[0]

    def read_uint64(self) -> int:
        """Read a 64-bit unsigned integer"""
        fmt = ">Q" if self.is_big_endian else "<Q"
        return struct.unpack(fmt, self.stream.read(8))[0]

    def read_single(self) -> float:
        """Read a 32-bit float"""
        fmt = ">f" if self.is_big_endian else "<f"
        return struct.unpack(fmt, self.stream.read(4))[0]

    def read_double(self) -> float:
        """Read a 64-bit double"""
        fmt = ">d" if self.is_big_endian else "<d"
        return struct.unpack(fmt, self.stream.read(8))[0]

    def read_bytes(self, count: int) -> bytes:
        return self.stream.read(count)

    def close(self):
        if self.stream:
            self.stream.close()


class ExtendedBinaryWriter:
    def __init__(self, stream: BinaryIO, is_big_endian: bool = False):
        self.stream = stream
        self.is_big_endian = is_big_endian
        self.offset = 0
        self.offsets: Dict[str, int] = {}

    @property
    def base_stream(self) -> BinaryIO:
        return self.stream

    def set_stream(self, stream: BinaryIO):
        self.stream = stream

    def set_endian(self, is_big_endian: bool):
        self.is_big_endian = is_big_endian

    def jump_to(self, position: int, absolute: bool = True):
        if absolute:
            self.stream.seek(position)
        else:
            self.stream.seek(position + self.offset)

    def jump_ahead(self, amount: int = 1):
        self.stream.seek(amount, 1)

    def jump_behind(self, amount: int = 1):
        self.stream.seek(-amount, 1)

    def add_offset(self, name: str, offset_length: int = 4):
        self.offsets[name] = self.stream.tell()
        self.write_nulls(offset_length)

    def has_offset(self, name: str) -> bool:
        return name in self.offsets

    def fill_in_offset(self, name: str, value: Optional[int] = None, absolute: bool = True, remove_offset: bool = True):
        if not self.has_offset(name):
            return

        cur_pos = self.stream.tell()

        if value is None:
            value = cur_pos

        self.stream.seek(self.offsets[name])

        if absolute:
            self.write_uint32(value)
        else:
            self.write_uint32(value - self.offset)

        if remove_offset:
            del self.offsets[name]

        self.stream.seek(cur_pos)

    def write_dal_signature(self, sig: str, size: int):
        self.write_signature(sig + " " * (size - len(sig)))

    def write_signature(self, signature: str):
        self.stream.write(signature.encode("ascii"))

    def write_null(self):
        """Write a single null byte"""
        self.stream.write(b"\x00")

    def write_nulls(self, count: int):
        """Write multiple null bytes"""
        self.stream.write(b"\x00" * count)

    def write_null_terminated_string(self, value: str):
        """Write a null-terminated string"""
        self.stream.write(value.encode("utf-8"))
        self.write_null()

    def fix_padding(self, amount: int = 4, offset: int = 0):
        if amount < 1:
            return

        pad_amount = 0
        while (self.stream.tell() + offset + pad_amount) % amount != 0:
            pad_amount += 1
        self.write_nulls(pad_amount)

    # Basic type writing methods
    def write_byte(self, value: int):
        """Write a single byte"""
        self.stream.write(struct.pack("B", value))

    def write_sbyte(self, value: int):
        """Write a signed byte"""
        self.stream.write(struct.pack("b", value))

    def write_bool(self, value: bool):
        """Write a boolean"""
        self.write_byte(1 if value else 0)

    def write_int16(self, value: int):
        """Write a 16-bit signed integer"""
        fmt = ">h" if self.is_big_endian else "<h"
        self.stream.write(struct.pack(fmt, value))

    def write_uint16(self, value: int):
        """Write a 16-bit unsigned integer"""
        fmt = ">H" if self.is_big_endian else "<H"
        self.stream.write(struct.pack(fmt, value))

    def write_int32(self, value: int):
        """Write a 32-bit signed integer"""
        fmt = ">i" if self.is_big_endian else "<i"
        self.stream.write(struct.pack(fmt, value))

    def write_uint32(self, value: int):
        """Write a 32-bit unsigned integer"""
        fmt = ">I" if self.is_big_endian else "<I"
        self.stream.write(struct.pack(fmt, value))

    def write_int64(self, value: int):
        """Write a 64-bit signed integer"""
        fmt = ">q" if self.is_big_endian else "<q"
        self.stream.write(struct.pack(fmt, value))

    def write_uint64(self, value: int):
        """Write a 64-bit unsigned integer"""
        fmt = ">Q" if self.is_big_endian else "<Q"
        self.stream.write(struct.pack(fmt, value))

    def write_single(self, value: float):
        """Write a 32-bit float"""
        fmt = ">f" if self.is_big_endian else "<f"
        self.stream.write(struct.pack(fmt, value))

    def write_double(self, value: float):
        """Write a 64-bit double"""
        fmt = ">d" if self.is_big_endian else "<d"
        self.stream.write(struct.pack(fmt, value))

    def write_bytes(self, data: bytes):
        self.stream.write(data)

    def write(self, data: bytes):
        self.stream.write(data)

    def start_deflate_encapsulation(self) -> BinaryIO:
        # Store the main stream
        main_stream = self.stream

        # Write ZLIB Header
        self.write_signature("ZLIB")
        self.add_offset("UncompressedSize")
        self.add_offset("CompressedSize")

        # Write ZLIB flags
        self.write_byte(0x78)
        self.write_byte(0xDA)

        # Set stream to buffer
        self.set_stream(BytesIO())

        # Return the main stream
        return main_stream

    def end_deflate_encapsulation(self, main_stream: BinaryIO):
        from .stream_tools import StreamTools

        # Record the amount of uncompressed data
        uncompressed_size = self.stream.tell()

        # Compress the data into the main stream and store the size
        compressed_size = StreamTools.deflate_compress(self.stream, main_stream)

        # Return the main stream back to the writer
        self.set_stream(main_stream)

        # Fill in the sizes into the header
        self.fill_in_offset("UncompressedSize", uncompressed_size)
        self.fill_in_offset("CompressedSize", compressed_size)

    def close(self):
        if self.stream:
            self.stream.close()
