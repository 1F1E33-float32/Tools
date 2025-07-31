import struct
import io
import re

def reverse_uint32(x):
    """Reverse (swap) the endianness of a 32‐bit unsigned integer."""
    return ((x & 0xFF) << 24) | (((x >> 8) & 0xFF) << 16) | (((x >> 16) & 0xFF) << 8) | ((x >> 24) & 0xFF)

def read_compressed_string(buffer, encoding='shift_jis'):
    """
    Read a compressed string from a byte buffer.
    The algorithm follows the C# logic: if the byte is between 0x81 and 0x9F,
    it reads the next byte as well; otherwise the byte is “unpacked”.
    """
    b_arr = bytearray()
    i = 0
    while i < len(buffer):
        c = buffer[i]
        i += 1
        if c == 0:
            break
        # In the C# code the condition is:
        #    if (c >= 0x81 && c <= 0x9F || (byte)(c + 0x20) <= 0xF)
        # In practice, only the 0x81-0x9F part is active.
        if 0x81 <= c <= 0x9F:
            b_arr.append(c)
            if i < len(buffer):
                b_arr.append(buffer[i])
                i += 1
        else:
            # "Unpack" the value.
            # Note: In C# the subtraction is performed with modulo 2^16 arithmetic.
            v0 = (c - 0x7D62) & 0xFFFF
            v1 = (v0 >> 8) & 0xFF
            v2 = v0 & 0xFF
            b_arr.append(v1)
            b_arr.append(v2)
    if not b_arr:
        return ""
    return b_arr.decode(encoding, errors='replace')

def read_cstring(buffer, encoding='shift_jis'):
    """Read a null-terminated string from a byte buffer."""
    null_index = buffer.find(b'\0')
    if null_index == -1:
        return buffer.decode(encoding, errors='replace')
    return buffer[:null_index].decode(encoding, errors='replace')

def escape_string(s):
    """Escape control characters so they can be exported to a text file."""
    return s.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")

def unespace_string(s):
    """Unescape strings that were exported (reverse of escape_string)."""
    return s.replace("\\r", "\r").replace("\\n", "\n").replace("\\t", "\t")

class Opcode:
    def __init__(self, addr, code, args=None):
        self.addr = addr          # original position relative to code base
        self.new_addr = None      # updated address during saving
        self.code = code          # opcode byte (integer)
        self.args = args          # any argument bytes (or None)

class Script:
    def __init__(self):
        self.opcodes = []             # list of Opcode objects
        self.encoding = 'shift_jis'   # used for string decoding/encoding

    def load(self, file_path):
        """Load a script from a binary file."""
        with open(file_path, 'rb') as f:
            data = f.read()
        stream = io.BytesIO(data)
        self._read(stream)

    def _read(self, stream):
        # Read the header: two 32-bit integers indicating table sizes.
        v1_bytes = stream.read(4)
        if len(v1_bytes) < 4:
            raise Exception("Unexpected end of file while reading v1")
        v1 = struct.unpack('<i', v1_bytes)[0]

        v2_bytes = stream.read(4)
        if len(v2_bytes) < 4:
            raise Exception("Unexpected end of file while reading v2")
        v2 = struct.unpack('<i', v2_bytes)[0]

        # Read offset tables.
        offset_table_0 = set()
        offset_table_1 = set()
        for _ in range(v1):
            entry = struct.unpack('<I', stream.read(4))[0]
            offset_table_0.add(entry)
        for _ in range(v2):
            entry = struct.unpack('<I', stream.read(4))[0]
            offset_table_1.add(entry)

        self.opcodes.clear()
        codebase = stream.tell()  # starting position of opcodes

        # Process opcodes until end-of-file.
        while stream.tell() < len(stream.getbuffer()):
            addr = stream.tell() - codebase
            code_byte = stream.read(1)
            if not code_byte:
                break
            code = code_byte[0]

            # Opcodes with no additional arguments.
            if code in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13,
                        0x17, 0x18,0x34, 0x35,0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43]:
                self.opcodes.append(Opcode(addr, code))
            # Opcodes that contain a string.
            elif code in [0x0A, 0x0B, 0x33]:
                args = self._read_cstring_from_stream(stream)
                self.opcodes.append(Opcode(addr, code, args))
            # Opcodes that have a 4-byte argument.
            elif code in [0x14, 0x15, 0x19, 0x1A, 0x1B, 0x32]:
                if code == 0x19:
                    if addr not in offset_table_0:
                        raise Exception("Address not found in table for opcode 0x19.")
                if code == 0x1A:
                    # For opcode 0x1A we expect the offset (addr + 1 + 4) to be present.
                    if (addr + 1 + 4) not in offset_table_1:
                        raise Exception("Address not found in table for opcode 0x1A.")
                args = stream.read(4)
                if len(args) < 4:
                    raise Exception("Unexpected end of file while reading 4-byte argument.")
                self.opcodes.append(Opcode(addr, code, args))
            # Opcode with a 1-byte argument.
            elif code == 0x1C:
                args = stream.read(1)
                if len(args) < 1:
                    raise Exception("Unexpected end of file while reading 1-byte argument.")
                self.opcodes.append(Opcode(addr, code, args))
            else:
                raise Exception(f"Unknown Opcode {code:02X}")

    def _read_cstring_from_stream(self, stream):
        """Read a null-terminated sequence of bytes from stream (including the null)."""
        bytes_list = bytearray()
        while True:
            byte = stream.read(1)
            if not byte:
                break
            bytes_list.extend(byte)
            if byte == b'\0':
                break
        return bytes(bytes_list)

    def get_strings(self):
        """
        Collect strings from opcodes.
        For opcode 0x0A, the bytes are “compressed” and require special unpacking.
        For opcodes 0x0B and 0x33, they are simple null-terminated strings.
        Returns a list of tuples: (opcode index, string).
        """
        result = []
        for index, opcode in enumerate(self.opcodes):
            if opcode.code == 0x0A:
                s = read_compressed_string(opcode.args, self.encoding)
                result.append((index, s))
            elif opcode.code in [0x0B, 0x33]:
                s = read_cstring(opcode.args, self.encoding)
                result.append((index, s))
        return result

    def export_strings(self, file_path, export_all):
        """
        Export strings from opcodes to a text file.
        If export_all is False, some strings (e.g. file names) may be skipped.
        Each string is output twice (using different markers) along with its opcode index.
        """
        strings = self.get_strings()
        with open(file_path, 'w', encoding='utf-8') as f:
            for index, s in strings:
                if not export_all:
                    # Skip strings whose first character is a basic ASCII character (or whitespace).
                    if s and ord(s[0]) < 0x81 and s[0] not in "\n\r\t":
                        continue
                esc = escape_string(s)
                f.write(f"◇{index:08X}◇{esc}\n")
                f.write(f"◆{index:08X}◆{esc}\n")
                f.write("\n")

if __name__ == "__main__":
    script = Script()
    script.load(r"D:\Fuck_galgame\script\S02_03.MES")
    
    script.export_strings("exported_strings.txt", export_all=True)