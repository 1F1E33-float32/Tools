import struct
import io

class YSTB_Arg_V5:
    def __init__(self, arg_id=0, arg_type=0, arg_size=0, raw_data=b''):
        self.arg_id = arg_id
        self.arg_type = arg_type
        self.arg_size = arg_size
        self.raw_data = raw_data

class YSTB_Inst_V5:
    def __init__(self, opcode=0, arg_count=0, u0=0, u1=0):
        self.opcode = opcode
        self.arg_count = arg_count
        self.u0 = u0
        self.u1 = u1
        self.args = []

def get_xor_key(file_obj):
    header_v5_size = 32
    header_data = file_obj.read(header_v5_size)
    if len(header_data) < header_v5_size:
        raise ValueError("File too small, cannot read V5 header.")

    sig, ver, instEntryCount, instIndexSize, argsIndexSize, argsDataSize, lineNumbersSize, reserve0 = \
        struct.unpack('<4sIIIIIII', header_data)

    # 如果没有 argsData，返回 0 表示不需要 XOR
    if argsDataSize == 0:
        return 0
    else:
        # 根据给定的偏移读取 4 字节的 XOR key
        offset = instIndexSize + header_v5_size + 0x8
        file_obj.seek(offset, 0)
        key_data = file_obj.read(4)
        if len(key_data) < 4:
            raise ValueError(f"File too small to read XOR key at offset {hex(offset)}.")
        key = struct.unpack('<I', key_data)[0]
        return key

def xor_ystb(data_ba, xor_key):
    magic = struct.unpack_from('<I', data_ba, 0)[0]
    version = struct.unpack_from('<I', data_ba, 4)[0]
    
    # magic 必须是 YSTB 0x42545359
    if magic != 0x42545359:
        return False
    
    key_bytes = struct.pack('<I', xor_key)
    header_format = '<4sIIIIIII'
    hdr_tuple = struct.unpack_from(header_format, data_ba, 0)

    uiInstIndexSize   = hdr_tuple[3]
    uiArgsIndexSize   = hdr_tuple[4]
    uiArgsDataSize    = hdr_tuple[5]
    uiLineNumbersSize = hdr_tuple[6]

    offset = struct.calcsize(header_format)

    # XOR instIndex
    for i in range(uiInstIndexSize):
        data_ba[offset + i] ^= key_bytes[i & 3]
    offset += uiInstIndexSize

    # XOR argsIndex
    for i in range(uiArgsIndexSize):
        data_ba[offset + i] ^= key_bytes[i & 3]
    offset += uiArgsIndexSize

    # XOR argsData
    for i in range(uiArgsDataSize):
        data_ba[offset + i] ^= key_bytes[i & 3]
    offset += uiArgsDataSize

    # XOR lineNumbers
    for i in range(uiLineNumbersSize):
        data_ba[offset + i] ^= key_bytes[i & 3]
    offset += uiLineNumbersSize

    return True

def parse_ystb_v5(data_ba):
    header_format = '<4sIIIIIII'
    hdr_size = struct.calcsize(header_format)
    sig, version, uiInstEntryCount, uiInstIndexSize, uiArgsIndexSize, uiArgsDataSize, uiLineNumbersSize, uiReserve0 = \
        struct.unpack_from(header_format, data_ba, 0)

    inst_list = []
    offset = hdr_size

    # 读取所有指令（instEntryCount 个）
    for _ in range(uiInstEntryCount):
        opcode, arg_count, u0, u1 = struct.unpack_from('<BBBB', data_ba, offset)
        offset += 4
        inst = YSTB_Inst_V5(opcode, arg_count, u0, u1)
        inst_list.append(inst)

    # 读取 arg index
    arg_index_count = uiArgsIndexSize // 12
    arg_index_offset = offset
    arg_data_offset  = offset + uiArgsIndexSize

    arg_index_list = []
    for _ in range(arg_index_count):
        arg_id, arg_type, arg_size, data_ofs = struct.unpack_from('<HHII', data_ba, arg_index_offset)
        arg_index_offset += 12

        cur_data_ptr = arg_data_offset + data_ofs
        raw_data = data_ba[cur_data_ptr : cur_data_ptr + arg_size]

        arg_obj = YSTB_Arg_V5(arg_id, arg_type, arg_size, raw_data)
        arg_index_list.append(arg_obj)

    # 将 arg 分配到对应的指令
    read_arg_idx = 0
    for inst in inst_list:
        for _ in range(inst.arg_count):
            inst.args.append(arg_index_list[read_arg_idx])
            read_arg_idx += 1

    return inst_list

def YSTB(file_path, opcode, idcode):
    with open(file_path, 'rb') as f:
        file_data = f.read()

    file_io = io.BytesIO(file_data)
    xor_key = get_xor_key(file_io)

    data_ba = bytearray(file_data)
    if xor_key != 0:
        xor_ystb(data_ba, xor_key)

    inst_list = parse_ystb_v5(data_ba)

    text_list = []
    voice_list = []
    is_find_text = False

    for inst in inst_list:
        if is_find_text:
            if len(inst.args) > 1:
                is_find_text = False
                continue
            text = inst.args[0].raw_data.decode('cp932')
            if "＠" in text:
                pass
            text_list.append(text)
            voice_list.append(voice)
            is_find_text = False

        if inst.opcode == opcode:
            if len(inst.args) < 5:
                continue
            arg_sign1 = inst.args[0]
            if arg_sign1.arg_id == 0 and arg_sign1.arg_size > 0 and arg_sign1.arg_type == 3 and b'es.SND' in arg_sign1.raw_data:
                arg_sign2 = inst.args[1]
                if arg_sign2.arg_id == 1 and arg_sign2.arg_size > 0 and arg_sign2.arg_type == 1 and b'B\x01\x00\x15' in arg_sign2.raw_data:
                    arg_sign3 = inst.args[3]
                    arg_sign4 = inst.args[4]
                    arg_sign5 = inst.args[5]
                    if arg_sign3.raw_data == arg_sign4.raw_data == arg_sign5.raw_data:
                        arg_voice = inst.args[2]
                        if arg_voice.arg_id == idcode and arg_voice.arg_size > 0:
                            if arg_voice.raw_data == bytearray(b"M\x02\x00\'\'"):
                                continue
                            voice = arg_voice.raw_data[3:].decode('cp932')
                            voice = voice.split('"')[1]
                            is_find_text = True

    return voice_list, text_list