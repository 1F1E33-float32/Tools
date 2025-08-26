import os
import re
import json
import zlib
import struct
import argparse
from io import BytesIO

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    parser.add_argument("-spk", type=str, default=r'D:\Fuck_galgame\soundconf.xml')
    return parser.parse_args(args=args, namespace=namespace)

class SceneLineType:
    COMMAND = 0x3001
    MESSAGE = 0x2001
    NAME = 0x2101
    INPUT = 0x0201
    PAGE = 0x0301

class CATSCENEHDR:
    STRUCT_FORMAT = '<8sii'  # Signature (8s), CompressedLength (int), DecompressedLength (int)
    SIZE = struct.calcsize(STRUCT_FORMAT)

    def __init__(self, signature: bytes, compressed_length: int, decompressed_length: int):
        self.signature_raw = signature
        self.compressed_length = compressed_length
        self.decompressed_length = decompressed_length

    @property
    def signature(self):
        # 去除空字符并解码为字符串
        return self.signature_raw.split(b'\x00', 1)[0].decode('cp932')

class SCRIPTHDR:
    STRUCT_FORMAT = '<iiii'  # ScriptLength (int), InputCount (int), OffsetTable (int), StringTable (int)
    SIZE = struct.calcsize(STRUCT_FORMAT)

    def __init__(self, script_length: int, input_count: int, offset_table: int, string_table: int):
        self.script_length = script_length
        self.input_count = input_count
        self.offset_table = offset_table
        self.string_table = string_table

    @property
    def entry_count(self):
        return (self.string_table - self.offset_table) // 4

class SCRIPTLINE:
    STRUCT_FORMAT = '<H'  # Type (unsigned short)
    SIZE = struct.calcsize(STRUCT_FORMAT)

    def __init__(self, type_: int, content: str):
        self.type = type_
        self.content = content

    def __str__(self):
        return f"0x{self.type:04X} \"{self.content}\""

class CstScene:
    def __init__(self, file_name, lines):
        self.file_name = file_name
        self.lines = lines
        self.count = len(lines)

    def decompile_internal(self):
        decompiled_data = []
        base_name = os.path.splitext(os.path.basename(self.file_name))[0]
        decompiled_data.append({'TYPE': 'HEADER', 'Content': f"#{base_name}"})
        decompiled_data.append({'TYPE': 'HEADER', 'Content': ''})  # 添加一个空行

        i = 0
        while i < self.count:
            line = self.lines[i]
            if line.type == SceneLineType.COMMAND:  # 12289
                line.content = re.sub(r'(?<=\bpcm\s)\d+\s', '', line.content)
                if not re.match(r'pcm\s+\d+\s+vol\s+.*', line.content):
                    decompiled_data.append({'TYPE': 'COMMAND', 'Content': line.content})

            elif line.type == SceneLineType.MESSAGE:  # 8193
                if line.content.startswith("\\n"):
                    decompiled_data.append({'TYPE': 'MESSAGE', 'Content': line.content[2:]})
                elif len(line.content) == 0:
                    i += 1
                    continue
                else:
                    decompiled_data.append({'TYPE': 'MESSAGE', 'Content': line.content})

            elif line.type == SceneLineType.NAME:  # 8449
                decompiled_data.append({'TYPE': 'NAME', 'Content': line.content})
                # 检查下一个条目是否是消息
                if (i + 1 < self.count) and (self.lines[i + 1].type == SceneLineType.MESSAGE):
                    next_line = self.lines[i + 1]
                    message_content = next_line.content
                    if message_content.startswith("\\n"):
                        message_content = message_content[2:]

                    elif len(message_content) == 0:
                        i += 1
                        continue

                    decompiled_data.append({'TYPE': 'MESSAGE', 'Content': message_content})
                    i += 1

            elif line.type == SceneLineType.INPUT:
                i += 1
                continue
                decompiled_data.append({'TYPE': 'INPUT', 'Content': ''})

            elif line.type == SceneLineType.PAGE:
                i += 1
                continue
                decompiled_data.append({'TYPE': 'PAGE', 'Content': '\\p'})

            else:
                i += 1
                continue
                decompiled_data.append({'TYPE': 'UNKNOWN', 'Content': f"<Unknown Type {line.type}> {line.content}"})

            i += 1

        return decompiled_data

def read_null_terminated_string(buffer, encoding='shift_jis'):
    chars = []
    while True:
        byte = buffer.read(1)
        if not byte or byte == b'\x00':
            break
        chars.append(byte)
    return b''.join(chars).decode(encoding, errors='replace')

def extract_cst(file_path):
    with open(file_path, 'rb') as f:
        # 读取 CATSCENEHDR
        hdr_data = f.read(CATSCENEHDR.SIZE)
        if len(hdr_data) != CATSCENEHDR.SIZE:
            raise Exception("File too short to contain CATSCENEHDR")
        signature, compressed_length, decompressed_length = struct.unpack(CATSCENEHDR.STRUCT_FORMAT, hdr_data)
        hdr = CATSCENEHDR(signature, compressed_length, decompressed_length)

        # 校验签名
        if hdr.signature != 'CatScene':
            raise ValueError(f"Invalid signature: {hdr.signature}")

        # 读取压缩数据
        compressed_data = f.read(hdr.compressed_length)
        if len(compressed_data) != hdr.compressed_length:
            raise Exception("File too short to contain compressed data")
        
        # 解压缩数据
        script_data = zlib.decompress(compressed_data)

        if len(script_data) != hdr.decompressed_length:
            raise Exception("Decompressed data length mismatch")

        buffer = BytesIO(script_data)

        # 读取 SCRIPTHDR
        script_hdr_data = buffer.read(SCRIPTHDR.SIZE)
        if len(script_hdr_data) != SCRIPTHDR.SIZE:
            raise Exception("Script data too short to contain SCRIPTHDR")
        script_length, input_count, offset_table, string_table = struct.unpack(SCRIPTHDR.STRUCT_FORMAT, script_hdr_data)
        script_hdr = SCRIPTHDR(script_length, input_count, offset_table, string_table)

        # 校验脚本长度
        if script_hdr.script_length + SCRIPTHDR.SIZE != len(script_data):
            raise Exception("Corrupted Script!")

        entry_count = script_hdr.entry_count

        # 定位到 OffsetTable
        buffer.seek(script_hdr.offset_table + SCRIPTHDR.SIZE)

        # 读取偏移表
        offsets = []
        for _ in range(entry_count):
            offset_data = buffer.read(4)  # 每个偏移为 4 字节
            if len(offset_data) != 4:
                raise Exception("Script data too short to contain all offsets")
            offset = struct.unpack('<I', offset_data)[0]
            offsets.append(offset)

        # 读取 SCRIPTLINE
        script_lines = []
        for i in range(entry_count):
            # 定位到当前条目的位置
            current_offset = offsets[i] + script_hdr.string_table + SCRIPTHDR.SIZE
            if current_offset >= len(script_data):
                raise Exception(f"Offset {current_offset} out of bounds")
            buffer.seek(current_offset)

            # 读取 Type
            type_data = buffer.read(SCRIPTLINE.SIZE)
            if len(type_data) != SCRIPTLINE.SIZE:
                raise Exception(f"Script data too short to contain Type at entry {i}")
            type_ = struct.unpack(SCRIPTLINE.STRUCT_FORMAT, type_data)[0]

            # 读取 Content
            content = read_null_terminated_string(buffer, encoding='cp932')

            script_lines.append(SCRIPTLINE(type_, content))

        return CstScene(file_path, script_lines)

def text_cleaning(text):
    text =  re.sub(r'\[([^]/]*)/([^]]*)\]', r'\1', text)
    text = re.sub(r'\\(?!w0)[a-zA-Z0-9]{2}', '', text)
    text = re.sub(r'\\w0;.*', '', text)
    text = text.replace('」', '').replace('「', '').replace('』', '').replace('『', '').replace('（', '').replace( '）', '')
    text = text.replace('\\@', '').replace('\\n', '').replace('♪', '').replace('　', '').replace('"', '').replace('①', '。').replace('●', '')
    text = re.sub(r'\[[^\[\]]*\]', '', text)
    return text

if __name__ == "__main__":
    args = parse_args()

    files = [os.path.join(root, file) for root, _, filenames in os.walk(args.JA) for file in filenames if file.lower().endswith('.cst')]

    results = []
    for file in files:
        cst = extract_cst(file)
        cst_sc = cst.decompile_internal()

        is_spk = False
        is_msg = False
        tmp_voice = []
        for i, item in enumerate(cst_sc):
            if item['TYPE'] == 'COMMAND' and item['Content'].startswith('pcm ') and not is_spk and not is_msg:
                is_spk = True
                tmp_voice.append(item['Content'][4:])

            elif item['TYPE'] == 'NAME' and is_spk and not is_msg:
                is_msg = True
                tmp_speaker = item['Content']
                tmp_speaker = tmp_speaker.split('＠')[0]
            
            elif item['TYPE'] == 'MESSAGE' and is_spk and is_msg:
                is_spk = False
                is_msg = False
                Text = text_cleaning(item['Content'])

                for voice in tmp_voice:
                    voice = voice.replace(' ', '')
                    Speaker = tmp_speaker
                            
                    results.append((Speaker, voice, Text))
                tmp_voice.clear()
                tmp_speaker = None

    with open(args.op, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            if Voice.lower() not in seen:
                seen.add(Voice.lower())
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)