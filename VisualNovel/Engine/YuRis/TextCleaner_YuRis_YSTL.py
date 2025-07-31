import struct

class YSTLHeader:
    def __init__(self, signature: str, version: int, entry_count: int):
        self.signature = signature
        self.version = version
        self.entry_count = entry_count

    def __repr__(self):
        return f"<YSTLHeader signature='{self.signature}' version={self.version} entry_count={self.entry_count}>"

class YSTLEntryV5:
    def __init__(
            self,
            uiSequence=0,
            uiPathSize=0,
            ucPathStr=b"",
            uiHighDateTime=0,
            uiLowDateTime=0,
            uiVariableCount=0,
            uiLabelCount=0,
            uiTextCount=0
            ):
        self.uiSequence = uiSequence
        self.uiPathSize = uiPathSize
        self.ucPathStr = ucPathStr
        self.uiHighDateTime = uiHighDateTime
        self.uiLowDateTime = uiLowDateTime
        self.uiVariableCount = uiVariableCount
        self.uiLabelCount = uiLabelCount
        self.uiTextCount = uiTextCount

    def get_path_str(self, encoding='cp932', slash='/'):
        decoded = self.ucPathStr.decode(encoding, errors='replace')
        decoded = decoded.replace('\\', slash)
        return decoded

    def __repr__(self):
        return (f"<YSTLEntryV5 seq={self.uiSequence} path='{self.get_path_str()}' textCount={self.uiTextCount}>")

def parse_ystl_v5(file_path: str):
    entries = []

    with open(file_path, 'rb') as f:
        data = f.read(4 + 4 + 4)
        if len(data) < 12:
            raise ValueError("文件头不足 12 字节，非合法 YSTL")
        
        sig_bytes, version, entry_count = struct.unpack('<4sII', data)
        signature = sig_bytes.decode('ascii', errors='replace')

        if signature != "YSTL":
            raise ValueError(f"Signature 不正确: {signature}")

        header = YSTLHeader(signature, version, entry_count)
 
        for i in range(entry_count):
            uiSequence = struct.unpack('<I', f.read(4))[0]
            uiPathSize = struct.unpack('<I', f.read(4))[0]
            ucPathStr = f.read(uiPathSize)
            # 剩余 5 个 uint32_t
            uiHighDateTime, uiLowDateTime, uiVariableCount, uiLabelCount, uiTextCount = struct.unpack('<IIIII', f.read(20))

            entry = YSTLEntryV5(uiSequence,
                                uiPathSize,
                                ucPathStr,
                                uiHighDateTime,
                                uiLowDateTime,
                                uiVariableCount,
                                uiLabelCount,
                                uiTextCount)
            entries.append(entry)

    return (header, entries)

def YSTL(file_path :str):
    header, entries = parse_ystl_v5(file_path)
    filelist = []
    for entry in entries:
        path_str = entry.get_path_str()

        if 'userscript' in path_str and entry.uiTextCount > 0:
            path_str = f"yst{entry.uiSequence:05d}.ybn"
            filelist.append(path_str)
    return filelist