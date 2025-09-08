import os
import struct
from tqdm import tqdm
from pathlib import Path
import numpy as np


class ArchiveEntry:
    def __init__(self, name="", offset=0, size=0, is_packed=False, unpacked_size=0):
        self.name = name
        self.offset = offset
        self.size = size
        self.is_packed = is_packed
        self.unpacked_size = unpacked_size
        self.type = ""  # 文件类型


class ArcExtractor:    
    # ARC文件头结构体 (0x24字节)
    ARC_HEADER_FORMAT = "<4sH4xI2xI4s8s"
    ARC_HEADER_SIZE = 0x24
    
    # NDIX段头结构体
    NDIX_HEADER_FORMAT = "<4sH"
    NDIX_HEADER_SIZE = 6
    
    # CADR段头结构体  
    CADR_HEADER_FORMAT = "<4sH"
    CADR_HEADER_SIZE = 6
    
    # 文件条目结构体
    FILE_ENTRY_FORMAT = "<H4xH"
    FILE_ENTRY_SIZE = 8
    
    # DATA段头结构体
    DATA_HEADER_FORMAT = "<4s20xI"
    DATA_HEADER_SIZE = 0x1E

    def __init__(self):
        self.entries = []

    def is_sane_count(self, count):
        return 0 < count <= 0x100000

    def unpack(self, input_file, output_dir):
        with open(input_file, "rb") as f:
            file_data = f.read()
        
        # 解析ARC文件
        if not self._parse_arc(file_data):
            print("ARC文件解析失败")
            return False
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 提取文件
        for entry in self.entries: 
            output_path = os.path.join(output_dir, entry.name)
            
            data = file_data[entry.offset : entry.offset + entry.size]
            
            with open(output_path, "wb") as f:
                f.write(data)

        return True

    def _parse_arc(self, file_data):
        """严格按C#实现解析ARC/XARC格式。"""
        # 检查基本长度
        if len(file_data) < 0x24:
            return False
        
        # 版本 0xA (Int16)
        version = struct.unpack('<H', file_data[0xA:0xC])[0]
        if version != 0x1001:
            return False
        
        # 计数 0x10 (Int32)
        count = struct.unpack('<I', file_data[0x10:0x14])[0]
        if not self.is_sane_count(count):
            return False
        
        # 模式 0xC (Int32)
        mode = struct.unpack('<I', file_data[0xC:0x10])[0]
        if (mode & 0xF) != 0:
            # 不支持的版本
            return False
        
        # DFNM 标识与 CADR 偏移
        if file_data[0x16:0x1A] != b'DFNM':
            return False
        if 0x22 > len(file_data):
            return False
        cadr_offset = struct.unpack('<Q', file_data[0x1A:0x22])[0]
        
        # NDIX 检查
        ndix_offset = 0x24
        if ndix_offset + 4 > len(file_data) or file_data[ndix_offset:ndix_offset + 4] != b'NDIX':
            return False
        
        # Reserve 检查 (确保 CADR 偏移在文件范围内)
        if cadr_offset > len(file_data):
            return False
        
        # CTIF 检查 (文件名块标识)
        index_length = 8 * count
        filenames_offset = ndix_offset + 8 + 2 * index_length
        if filenames_offset + 4 > len(file_data) or file_data[filenames_offset:filenames_offset + 4] != b'CTIF':
            return False
        
        # CADR 分段检查
        cadr_size = 4 + 12 * count
        if cadr_offset + cadr_size > len(file_data):
            return False
        if file_data[cadr_offset:cadr_offset + 4] != b'CADR':
            return False
        
        # 进入NDIX/CADR条目解析
        ndix_pos = ndix_offset + 6
        cadr_pos = cadr_offset + 6
        self.entries = []
        
        for i in range(count):
            # 文件名条目偏移 (NDIX 表中的值)
            if ndix_pos + 4 > len(file_data):
                return False
            entry_offset = struct.unpack('<I', file_data[ndix_pos:ndix_pos + 4])[0]
            
            # 条目头检查 (version == 0x1001)
            if entry_offset + 8 > len(file_data):
                return False
            if struct.unpack('<H', file_data[entry_offset:entry_offset + 2])[0] != 0x1001:
                return False
            
            # 文件名长度
            name_length = struct.unpack('<H', file_data[entry_offset + 6:entry_offset + 8])[0]
            name_start = entry_offset + 0xA
            name_end = name_start + name_length
            if name_end > len(file_data):
                return False
            
            # 文件名解密 (XOR 0x56)
            arr = np.frombuffer(file_data, dtype=np.uint8, count=name_length, offset=name_start)
            name_bytes_dec = (arr ^ 0x56).tobytes()
            try:
                name = name_bytes_dec.decode('cp932')
            except UnicodeDecodeError:
                name = name_bytes_dec.decode('cp932', errors='replace')
            
            # 读取文件数据偏移 (来自 CADR 表，步长 12)
            if cadr_pos + 8 > len(file_data):
                return False
            file_offset = struct.unpack('<Q', file_data[cadr_pos:cadr_pos + 8])[0]
            if file_offset >= len(file_data):
                return False
            
            self.entries.append(ArchiveEntry(name=name, offset=file_offset))
            
            ndix_pos += 8
            cadr_pos += 12
        
        # 为每个条目读取 DATA 段，确定大小与数据起点
        for entry in self.entries:
            if entry.offset + 4 > len(file_data) or file_data[entry.offset:entry.offset + 4] != b'DATA':
                return False
            if entry.offset + 0x1C > len(file_data):
                return False
            entry.size = struct.unpack('<I', file_data[entry.offset + 0x18:entry.offset + 0x1C])[0]
            entry.offset += 0x1E
        
        return True

    def _parse_ndix(self, file_data, ndix_offset, count, cadr_offset):
        if file_data[ndix_offset:ndix_offset + 4] != b'NDIX':
            return False
        
        if cadr_offset + self.CADR_HEADER_SIZE > len(file_data):
            return False
        
        if file_data[cadr_offset:cadr_offset + 4] != b'CADR':
            return False
        
        index_length = 8 * count
        filenames_offset = ndix_offset + 8 + 2 * index_length
        
        if filenames_offset + 4 > len(file_data):
            return False
        
        if file_data[filenames_offset:filenames_offset + 4] != b'CTIF':
            return False
        
        self.entries = []
        ndix_pos = ndix_offset + self.NDIX_HEADER_SIZE
        cadr_pos = cadr_offset + self.CADR_HEADER_SIZE
        
        for i in range(count):
            entry_offset = struct.unpack("<I", file_data[ndix_pos:ndix_pos + 4])[0]
            
            if not self._parse_file_entry(file_data, entry_offset, cadr_pos):
                return False
            
            ndix_pos += 8
            cadr_pos += 12
        
        for entry in self.entries:
            if not self._parse_data_section(file_data, entry):
                return False
        
        return True

    def _parse_file_entry(self, file_data, entry_offset, cadr_pos):
        if entry_offset + 8 > len(file_data):
            return False
        
        version, name_length = struct.unpack(self.FILE_ENTRY_FORMAT, file_data[entry_offset:entry_offset + self.FILE_ENTRY_SIZE])
        
        if version != 0x1001:
            return False
        
        name_offset = entry_offset + 0xA
        if name_offset + name_length > len(file_data):
            return False
        
        arr = np.frombuffer(file_data, dtype=np.uint8, count=name_length, offset=name_offset)
        name_bytes_dec = (arr ^ 0x56).tobytes()
        
        try:
            name = name_bytes_dec.decode("cp932")
        except UnicodeDecodeError:
            name = name_bytes_dec.decode("cp932", errors="replace")
        
        file_offset = struct.unpack("<Q", file_data[cadr_pos:cadr_pos + 8])[0]
        
        if file_offset >= len(file_data):
            return False
        
        entry = ArchiveEntry(name=name, offset=file_offset)
        self.entries.append(entry)
        
        return True

    def _parse_data_section(self, file_data, entry):
        if entry.offset + self.DATA_HEADER_SIZE > len(file_data):
            return False
        
        if file_data[entry.offset:entry.offset + 4] != b'DATA':
            return False
        
        entry.size = struct.unpack("<I", file_data[entry.offset + 0x18:entry.offset + 0x1C])[0]
        entry.offset += self.DATA_HEADER_SIZE
        
        return True


class KotoriExtractor:    
    # 音频文件偏移表条目结构体 (6字节)
    OFFSET_ENTRY_SIZE = 6

    def __init__(self):
        self.entries = []

    def is_sane_count(self, count):
        return 0 < count <= 0x100000

    def unpack(self, input_file, output_dir):
        with open(input_file, "rb") as f:
            file_data = f.read()
        
        if not self._parse_kotori(file_data, input_file):
            print("KOTORI文件解析失败")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        for entry in self.entries:
            output_path = os.path.join(output_dir, entry.name)
            
            data = self._extract_audio_entry(file_data, entry)
            
            with open(output_path, "wb") as f:
                f.write(data)

        return True

    def _parse_kotori(self, file_data, filename):
        # C#: if (!file.View.AsciiEqual (0, "KOTORI") || 0x1A1A00 != file.View.ReadInt32 (6))
        if len(file_data) < 0x18:
            return False
        
        # 检查"KOTORI"签名在偏移0
        if file_data[0:6] != b"KOTORI":
            return False
        
        # 检查魔数0x1A1A00在偏移6 (ReadInt32)
        magic1 = struct.unpack("<I", file_data[6:10])[0]
        if magic1 != 0x1A1A00:
            return False
        
        # 检查魔数0x0100A618在偏移0x10 (ReadInt32)
        if len(file_data) < 0x14:
            return False
        magic2 = struct.unpack("<I", file_data[0x10:0x14])[0]
        if magic2 != 0x0100A618:
            return False
        
        # 读取文件数量在偏移0x14 (ReadUInt16)
        if len(file_data) < 0x16:
            return False
        count = struct.unpack("<H", file_data[0x14:0x16])[0]
        if not self.is_sane_count(count):
            return False
        
        # 解析偏移表
        if not self._parse_offset_table(file_data, count, filename):
            return False
        
        return True

    def _parse_offset_table(self, file_data, count, filename):
        base_name = Path(filename).stem
        self.entries = []
        
        current_offset = 0x18
        
        if current_offset + 4 > len(file_data):
            return False
        
        next_offset = struct.unpack("<I", file_data[current_offset:current_offset + 4])[0]
        
        for i in range(count):
            entry = ArchiveEntry()
            entry.name = f"{base_name}_{i + 1:04d}.ogg"
            entry.type = "audio"
            entry.offset = next_offset
            
            if i + 1 != count:
                current_offset += self.OFFSET_ENTRY_SIZE
                if current_offset + 4 > len(file_data):
                    return False
                next_offset = struct.unpack("<I", file_data[current_offset:current_offset + 4])[0]
            else:
                next_offset = len(file_data)
            
            entry.size = next_offset - entry.offset
            
            if entry.size >= 0x32:
                entry.is_packed = True
                entry.unpacked_size = entry.size - 0x32
            
            if entry.offset + entry.size > len(file_data):
                return False
            
            self.entries.append(entry)
        
        return True

    def _extract_audio_entry(self, file_data, entry):
        # C#: if (entry.Size < 0x32 || ...)
        if entry.size < 0x32:
            return file_data[entry.offset:entry.offset + entry.size]
        
        # C#: !arc.File.View.AsciiEqual (entry.Offset, "KOTORi")
        if file_data[entry.offset:entry.offset + 6] != b"KOTORi":
            return file_data[entry.offset:entry.offset + entry.size]
        
        # C#: 0x001A1A00 != arc.File.View.ReadInt32 (entry.Offset+6)
        magic1 = struct.unpack("<I", file_data[entry.offset + 6:entry.offset + 10])[0]
        if magic1 != 0x001A1A00:
            return file_data[entry.offset:entry.offset + entry.size]
        
        # C#: 0x0100A618 != arc.File.View.ReadInt32 (entry.Offset+0x10)
        magic2 = struct.unpack("<I", file_data[entry.offset + 0x10:entry.offset + 0x14])[0]
        if magic2 != 0x0100A618:
            return file_data[entry.offset:entry.offset + entry.size]
        
        # C#: var key = new byte[0x10]; arc.File.View.Read (entry.Offset+0x20, key, 0, 0x10);
        key = file_data[entry.offset + 0x20:entry.offset + 0x30]
        
        # C#: uint length = entry.Size - 0x32;
        length = entry.size - 0x32
        
        # C#: arc.File.View.Read (entry.Offset+0x32, data, 0, length);
        data_arr = np.frombuffer(file_data, dtype=np.uint8, count=length, offset=entry.offset + 0x32).copy()
        key_arr = np.frombuffer(key, dtype=np.uint8)
        repeated_key = np.resize(key_arr[:16], length)
        data_arr ^= repeated_key
        return data_arr.tobytes()

def process_game_files(root_path, output_dir):
    # 处理DATA/rio.arc文件
    arc_file = os.path.join(root_path, "DATA", "rio.arc")
    script_output_dir = os.path.join(output_dir, "script")
    
    os.makedirs(script_output_dir, exist_ok=True)
        
    arc_extractor = ArcExtractor()
    arc_extractor.unpack(arc_file, script_output_dir)

    # 处理VOICE文件夹下的Kotori封包
    voice_dir = os.path.join(root_path, "VOICE")
    voice_output_dir = os.path.join(output_dir, "voice")
    
    os.makedirs(voice_output_dir, exist_ok=True)
        
    kotori_extractor = KotoriExtractor()
    voice_files = [f for f in os.listdir(voice_dir) if os.path.isfile(os.path.join(voice_dir, f))]
    
    for voice_file in tqdm(voice_files, ncols=150):
        voice_file_path = os.path.join(voice_dir, voice_file)
        kotori_extractor.unpack(voice_file_path, voice_output_dir)


if __name__ == "__main__":
    root_path = r"D:\GAL\2010_01\Kikouyoku Senki Tenkuu no Yumina FD  -ForeverDreams-"
    output_dir = r"D:\Fuck_galgame"

    process_game_files(root_path, output_dir)