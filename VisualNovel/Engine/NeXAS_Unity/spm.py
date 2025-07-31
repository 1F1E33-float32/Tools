import os

class AlicePackageFile:
    class PFHeader:
        def __init__(self, file_name, read_start_byte_pos, byte_length):
            self.file_name = file_name
            self.read_start_byte_pos = read_start_byte_pos
            self.byte_length = byte_length

        def __repr__(self):
            return f"PFHeader(file_name={self.file_name!r}, read_start_byte_pos={self.read_start_byte_pos}, byte_length={self.byte_length})"

    def __init__(self, file_path):
        self.file_path = file_path
        self.header_dict = {}  # Similar to Dictionary<string, PFHeader>
        self.parsing_pack(file_path)

    def parsing_pack(self, file_path):
        # Determine total file size
        file_size = os.path.getsize(file_path)
        
        with open(file_path, "rb") as f:
            # Skip first 16 bytes (assumed to be a file header or metadata)
            f.seek(16, os.SEEK_SET)

            while f.tell() < file_size:
                # Read 32 bytes for the file name field (potentially null-terminated)
                name_bytes = f.read(32)
                if len(name_bytes) < 32:
                    # Exit loop if we didn't get a full 32-byte record (could be corrupted or end-of-file)
                    break

                # Find the first null byte (0) to determine the end of the actual file name
                null_index = name_bytes.find(b'\x00')
                if null_index == -1:
                    # If no null terminator is found, use the full 32 bytes
                    actual_name_bytes = name_bytes
                else:
                    actual_name_bytes = name_bytes[:null_index]
                
                # Decode file name using UTF-8 encoding
                file_name = actual_name_bytes.decode("utf-8")

                # Read next 8 bytes for the starting byte (as a little-endian 64-bit integer)
                start_bytes = f.read(8)
                if len(start_bytes) < 8:
                    break
                # Convert the bytes to an integer (assuming little-endian)
                start_int = int.from_bytes(start_bytes, byteorder="little", signed=False)

                # Read following 8 bytes for the byte length field
                length_bytes = f.read(8)
                if len(length_bytes) < 8:
                    break
                byte_length = int.from_bytes(length_bytes, byteorder="little", signed=False)

                # Adjust the read start position by adding 16 (as done in the C# code)
                read_start_byte_pos = start_int + 16

                # Create a PFHeader object
                header = AlicePackageFile.PFHeader(file_name, read_start_byte_pos, byte_length)

                # Add header to the dictionary using file_name as key
                self.header_dict[file_name] = header

                # Skip forward by byte_length bytes (this moves the stream position ahead)
                f.seek(byte_length, os.SEEK_CUR)

if __name__ == "__main__":
    file_path = r"D:\青夏轨迹v2 R18\SPM.pac"
    try:
        pack = AlicePackageFile(file_path)
        print("Parsed header dictionary:")
        for key, header in pack.header_dict.items():
            print(key, ":", header)
    except Exception as e:
        print("Error reading package file:", e)