import os
from io import BytesIO
from typing import BinaryIO, Dict, List, Optional

from ..Exceptions.signature_mismatch_exception import SignatureMismatchException
from ..IO.extended_binary import ExtendedBinaryReader, ExtendedBinaryWriter
from ..IO.virtual_stream import VirtualStream
from .file_base import FileBase


class FileEntry:
    def __init__(self):
        self.file_name: str = ""
        self.data_position: int = 0
        self.data_length: int = 0
        self.data: Optional[bytes] = None

    def __str__(self):
        return self.file_name


class PCKFile(FileBase):
    def __init__(self):
        super().__init__()

        # Internal reader for streaming files from the archive
        self._internal_reader: Optional[ExtendedBinaryReader] = None

        # Options
        # Toggle for using larger signatures (0x14) or smaller ones (0x08)
        # DAL: RR uses larger signatures
        self.use_small_sig = False
        self.signature_size = -1
        self.padding_size = -1
        self.compress = False

        self.file_name_substitutions: Dict[str, str] = {"\\": "-backslash-"}

        self.file_entries: List[FileEntry] = []

    def load_from_reader(self, reader: ExtendedBinaryReader, keep_open: bool = False):
        # Store the current reader
        self._internal_reader = reader

        # Filename Section
        # This section contains an array of addresses to each of the file's name and the strings
        # itself right after, this section is only used for finding file indices from within game

        # This is a workaround for reading different versions of PCK files as some files seem to
        # have smaller padding (0x08 for Signatures, 0x04 for Padding)
        # while DAL: RR has larger padding (0x14 for Signatures, 0x08 for Padding)
        # This workaround works by checking the padding in the signature to determine the version
        self.signature_size = reader.check_dal_signature("Filename")
        if self.signature_size < 0x14:
            self.use_small_sig = True

        self.padding_size = self.padding_size if self.padding_size != -1 else (0x04 if self.use_small_sig else 0x08)

        # The length of the Filename section
        file_name_section_size = reader.read_int32()
        # Address to the list of filenames
        file_name_section_address = reader.get_position()

        # Pack Section
        # This section contains an array of file information and then all of its data

        reader.jump_to(file_name_section_size)
        reader.fix_padding(self.padding_size)

        # Check Signature
        pack_sig = reader.read_dal_signature("Pack")
        if pack_sig != "Pack" and len(pack_sig) <= 4:
            self._guess_padding(reader, "Pack")

            pack_sig = reader.read_dal_signature("Pack")
            if pack_sig != "Pack" and len(pack_sig) <= 4:
                raise SignatureMismatchException("Pack", pack_sig)

        # The length of the Pack section
        _ = reader.read_int32()
        file_count = reader.read_int32()

        # Read file entries
        for i in range(file_count):
            entry = FileEntry()
            entry.data_position = reader.read_int32()
            entry.data_length = reader.read_int32()
            self.file_entries.append(entry)

        # Jump back to the Filename section so we can get all of the file names
        reader.jump_to(file_name_section_address)

        # Reads all the file names
        for i in range(file_count):
            position = reader.read_int32() + file_name_section_address
            self.file_entries[i].file_name = reader.read_string_elsewhere(position)

        # Load all data into memory if the loader plans to close the stream
        if not keep_open:
            self.preload()

    def save_from_writer(self, writer: ExtendedBinaryWriter):
        # Loads all files into memory if not already
        # This is needed to ensure the reading stream is closed
        self.preload()

        # ZLIB Compression
        main_stream = None
        if self.compress:
            main_stream = writer.start_deflate_encapsulation()

        self.signature_size = self.signature_size if self.signature_size != -1 else (0x08 if self.use_small_sig else 0x14)
        self.padding_size = self.padding_size if self.padding_size != -1 else (0x04 if self.use_small_sig else 0x08)

        # Filename Section
        # Address of the Filename section
        section_position = writer.base_stream.tell()
        writer.write_dal_signature("Filename", self.signature_size)
        writer.add_offset("SectionSize")

        file_name_section_address = writer.base_stream.tell()

        # Allocates space for all the file name pointers
        for entry in self.file_entries:
            writer.add_offset(entry.file_name)

        # Fills in all the file names
        for entry in self.file_entries:
            # Fill in the address and write the file name (including paths)
            writer.fill_in_offset(entry.file_name, writer.base_stream.tell() - file_name_section_address)
            writer.write_null_terminated_string(entry.file_name)

        # Fills in the size of the Filename section
        writer.fill_in_offset("SectionSize")
        # Realigns the writer
        writer.fix_padding(self.padding_size, section_position)

        # Pack Section
        # Address to the Pack section
        section_position = writer.base_stream.tell()
        writer.write_dal_signature("Pack", self.signature_size)
        writer.add_offset("SectionSize")
        writer.write_int32(len(self.file_entries))

        # Writes file data entries
        for i in range(len(self.file_entries)):
            # Allocates 4 bytes for the absolute address of the contents of the file
            writer.add_offset(f"DataPtr{i}")
            # Writes the length of the file
            writer.write_int32(len(self.file_entries[i].data))

        # Fills in the size of the Pack section
        writer.fill_in_offset("SectionSize", writer.base_stream.tell() - section_position)
        # Realigns the writer
        writer.fix_padding(self.padding_size, section_position)

        # Data
        for i in range(len(self.file_entries)):
            writer.fill_in_offset(f"DataPtr{i}")
            writer.write_bytes(self.file_entries[i].data)
            # Realigns the writer
            writer.fix_padding(self.padding_size, section_position)

        # Finalise ZLIB Compression
        if self.compress:
            writer.end_deflate_encapsulation(main_stream)

    def preload(self):
        for entry in self.file_entries:
            # Check if file is already loaded into memory
            if entry.data is not None:
                continue
            self._internal_reader.jump_to(entry.data_position)
            entry.data = self._internal_reader.read_bytes(entry.data_length)

        if self._internal_reader:
            self._internal_reader.close()
            self._internal_reader = None

    def get_file_data(self, name_or_index) -> Optional[bytes]:
        if isinstance(name_or_index, str):
            # Get File Entry by filename
            entry = None
            for e in self.file_entries:
                if e.file_name.lower() == name_or_index.lower():
                    entry = e
                    break

            # Check if file is found
            if entry is None:
                return None

            # Check if preloaded
            if entry.data is not None:
                return entry.data

            self._internal_reader.jump_to(entry.data_position)
            return self._internal_reader.read_bytes(entry.data_length)
        else:
            # Get File Entry by index
            entry = self.file_entries[name_or_index]

            # Check if preloaded
            if entry.data is not None:
                return entry.data

            self._internal_reader.jump_to(entry.data_position)
            return self._internal_reader.read_bytes(entry.data_length)

    def get_file_stream(self, name_or_index) -> Optional[BinaryIO]:
        if isinstance(name_or_index, str):
            # Get File Entry by filename
            entry = None
            for e in self.file_entries:
                if e.file_name.lower() == name_or_index.lower():
                    entry = e
                    break

            if entry is None:
                return None

            # Return a memory stream if the reader is closed, assuming all files are loaded into memory
            if self._internal_reader is None:
                return BytesIO(entry.data)

            self._internal_reader.jump_to(entry.data_position)
            return VirtualStream(self._internal_reader.base_stream, entry.data_position, entry.data_length, True)
        else:
            # Get File Entry by index
            entry = self.file_entries[name_or_index]

            # Return a memory stream if the reader is closed, assuming all files are loaded into memory
            if self._internal_reader is None:
                return BytesIO(entry.data)

            self._internal_reader.jump_to(entry.data_position)
            return VirtualStream(self._internal_reader.base_stream, entry.data_position, entry.data_length, True)

    def extract_all_files(self, path: str):
        for entry in self.file_entries:
            file_path = os.path.join(path, self._perform_string_substitutions(entry.file_name, True))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            if entry.data is None:
                self._internal_reader.jump_to(entry.data_position)
                data = self._internal_reader.read_bytes(entry.data_length)
                with open(file_path, "wb") as f:
                    f.write(data)
            else:
                with open(file_path, "wb") as f:
                    f.write(entry.data)

    def add_all_files(self, path: str):
        # Collect all files
        all_files = []

        # Walk through all directories
        for root, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                # Get relative path
                rel_path = os.path.relpath(full_path, path)
                # Convert to forward slashes
                rel_path = rel_path.replace("\\", "/")
                all_files.append((rel_path, full_path))

        # Sort files (uppercase first, then lowercase)
        all_files.sort(key=lambda x: (0 if x[0][0].isupper() else 1, x[0]))

        # Add files to archive
        for rel_path, full_path in all_files:
            entry = FileEntry()
            entry.file_name = self._perform_string_substitutions(rel_path, False)
            with open(full_path, "rb") as f:
                entry.data = f.read()
            entry.data_length = len(entry.data)
            self.file_entries.append(entry)

        self._sort_file_list()

    def _sort_file_list(self):
        # Check if this is a face.mpb archive
        if any(e.file_name == "face.mpb" for e in self.file_entries):
            order = [".mpb", ".tex", "layername.bin", "screen.txt", ".exl", ".uca.bin", "Config.txt", ".amb", ""]
            self.file_entries.sort(key=lambda e: next((i for i, ext in enumerate(order) if e.file_name.endswith(ext)), len(order)))

        # Check if this is a .MA archive
        if any(e.file_name.endswith(".MA") for e in self.file_entries):
            order = [".MA", ""]
            self.file_entries.sort(key=lambda e: next((i for i, ext in enumerate(order) if e.file_name.endswith(ext)), len(order)))

    def add_file(self, filename: str, data: bytes):
        entry = FileEntry()
        entry.file_name = filename
        entry.data = data
        entry.data_length = len(data)
        self.file_entries.append(entry)

    def replace_file(self, filename: str, data: bytes):
        # Get File Entry by filename
        entry = None
        for e in self.file_entries:
            if e.file_name.lower() == filename.lower():
                entry = e
                break

        # If file is not found, Create a new one
        if entry is None:
            self.add_file(filename, data)
        else:
            entry.data = data
            entry.data_length = len(data)

    def search_for_file(self, contains_string: str) -> Optional[str]:
        for entry in self.file_entries:
            if contains_string.lower() in entry.file_name.lower():
                return entry.file_name
        return None

    def _perform_string_substitutions(self, file_name: str, direction: bool) -> str:
        if direction:
            for key, value in self.file_name_substitutions.items():
                file_name = file_name.replace(key, value)
        else:
            for key, value in self.file_name_substitutions.items():
                file_name = file_name.replace(value, key)
        return file_name

    def _guess_padding(self, reader: ExtendedBinaryReader, signature: str):
        start_position = reader.get_position()
        padding_options = [0x08, 0x10, 0x14]

        for padding in padding_options:
            reader.fix_padding(padding)
            if reader.peek_signature(len(signature)) == signature:
                self.padding_size = padding
                break
            reader.jump_to(start_position)

        reader.jump_to(start_position)

    def dispose(self):
        if self._internal_reader is not None:
            self._internal_reader.close()
            self._internal_reader = None
        self.file_entries.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
        return False
