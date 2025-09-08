import os
import re
import json
import struct
from typing import List, Optional, Dict, Any

class Section:
    def __init__(self, beg: int, end: int):
        self.beg = beg
        self.end = end

    def its(self, key: int) -> bool:
        # 如果 beg 和 end 均为 0xFF，则返回 False（空区域）
        if self.beg == 0xFF and self.end == 0xFF:
            return False
        return self.beg <= key <= self.end

class ScriptInfo:
    def __init__(self, name: str, version: int, uint8x2: tuple, uint8str: tuple, string: tuple, encstr: tuple, uint16x4: tuple, optunenc: int):
        self.name = name
        self.version = version
        self.uint8x2 = Section(*uint8x2)
        self.uint8str = Section(*uint8str)
        self.string = Section(*string)
        self.encstr = Section(*encstr)
        self.uint16x4 = Section(*uint16x4)
        self.optunenc = optunenc

    @staticmethod
    def query_by_name(name: str) -> Optional['ScriptInfo']:
        for info in ScriptInfo.infos:
            if info.name == name:
                return info
        return None

    @staticmethod
    def query_by_version(version: int) -> Optional['ScriptInfo']:
        for info in ScriptInfo.infos:
            if info.version == version:
                return info
        return None

ScriptInfo.infos = [
    #           name       ver     uint8x2        uint8str      string        encstr       uint16x4      optunenc
    ScriptInfo("dcpc",     0x3D63, (0x00, 0x2C), (0xFF, 0xFF), (0x2D, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x44), # D.C.P.C. ~Da Capo Plus Communication~
    ScriptInfo("dcws",     0x656C, (0x00, 0x2B), (0x2C, 0x31), (0x32, 0x4C), (0x4D, 0x50), (0x51, 0xFF), 0x48), # D.C. White Season ~Da Capo White Season~
    ScriptInfo("dcsv",     0x636C, (0x00, 0x2B), (0x2C, 0x31), (0x32, 0x4C), (0x4D, 0x50), (0x51, 0xFF), 0x46), # 
    ScriptInfo("dcas",     0x4E69, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x43),
    ScriptInfo("dcos",     0x315D, (0x00, 0x2B), (0xFF, 0xFF), (0x2C, 0x45), (0x46, 0x49), (0x4A, 0xFF), 0x42),
    ScriptInfo("dc2sc",    0x3B69, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x45),
    ScriptInfo("dc2fl",    0x9C69, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x45),
    ScriptInfo("dc2pc",    0x9969, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x45),

    ScriptInfo("ffexa",    0x7B69, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x43),
    ScriptInfo("ffexs",    0x7B6B, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x4B), (0x4C, 0x4F), (0x50, 0xFF), 0x43),
    ScriptInfo("ef",       0x466A, (0x00, 0x28), (0x2A, 0x2F), (0x30, 0x4A), (0x4B, 0x4E), (0x4F, 0xFF), 0x46),

    ScriptInfo("ktlep",    0x6E69, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x45),
    ScriptInfo("dcmems",   0x315D, (0x00, 0x2B), (0xFF, 0xFF), (0x2C, 0x45), (0x46, 0x49), (0x4A, 0xFF), 0x42),
    ScriptInfo("dcdx",     0x7769, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), 0x45),
    ScriptInfo("dcbs",     0x3163, (0x00, 0x2B), (0xFF, 0xFF), (0x2C, 0x48), (0x49, 0x4C), (0x4D, 0xFF), None),
    ScriptInfo("dc2bs",    0x316C, (0x00, 0x2B), (0x2C, 0x31), (0x32, 0x4C), (0x4D, 0x50), (0x51, 0xFF), None),
    ScriptInfo("dc2dm",    0x9D72, (0x00, 0x29), (0x2A, 0x31), (0x32, 0x4C), (0x4D, 0x50), (0x51, 0xFF), 0x44),
    ScriptInfo("dc2fy",    0x3866, (0x00, 0x2E), (0xFF, 0xFF), (0x2F, 0x4B), (0x4C, 0x4F), (0x50, 0xFF), 0x48),
    ScriptInfo("dc2cckko", 0x026C, (0x00, 0x2B), (0x2C, 0x31), (0x32, 0x4C), (0x4D, 0x50), (0x51, 0xFF), None),
    ScriptInfo("dc2ccotm", 0x016C, (0x00, 0x2B), (0x2C, 0x31), (0x32, 0x4C), (0x4D, 0x50), (0x51, 0xFF), None),
    ScriptInfo("dc2ty",    0x5F69, (0x00, 0x28), (0x29, 0x2E), (0x2F, 0x49), (0x4A, 0x4D), (0x4E, 0xFF), None),
    ScriptInfo("dc3rx",    0x9772, (0x00, 0x2B), (0x2C, 0x33), (0x34, 0x4E), (0x4F, 0x52), (0x53, 0xFF), 0x45),
    ScriptInfo("dc3pp",    0x9872, (0x00, 0x2A), (0x2B, 0x32), (0x33, 0x4E), (0x4F, 0x51), (0x52, 0xFF), 0x45),
    ScriptInfo("dc3wy",    0xA09F, (0x00, 0x38), (0x39, 0x41), (0x42, 0x5F), (0x60, 0x63), (0x64, 0xFF), 0x55),
    ScriptInfo("dc3dd",    0xA5A8, (0x00, 0x38), (0x39, 0x43), (0x44, 0x62), (0x63, 0x67), (0x68, 0xFF), 0x58),
    ScriptInfo("dc4",      0xAAB6, (0x00, 0x3A), (0x3B, 0x47), (0x48, 0x68), (0x69, 0x6D), (0x6E, 0xFF), 0x5D),
    ScriptInfo("dc4ph",    0xABB6, (0x00, 0x3A), (0x3B, 0x47), (0x48, 0x68), (0x69, 0x6D), (0x6E, 0xFF), 0x5D),
    ScriptInfo("ds",       0x9F9A, (0x00, 0x38), (0x39, 0x4A), (0x41, 0x5E), (0x5F, 0x62), (0x63, 0xFF), 0x54),
    ScriptInfo("dsif",     0xA1A1, (0x00, 0x39), (0x3A, 0x42), (0x43, 0x60), (0x61, 0x64), (0x65, 0xFF), 0x56),
    ScriptInfo("tmpl",     0xA6B4, (0x00, 0x3B), (0x3A, 0x46), (0x46, 0x67), (0x68, 0x6E), (0x6D, 0xFF), 0x5C),

    ScriptInfo("pp",       0x5B6C, (0x00, 0x28), (0x29, 0x2F), (0x30, 0x4A), (0x4B, 0x4E), (0x4F, 0xFF), 0x46),
]

class Token:
    def __init__(self, offset: int, value: int):
        self.offset = offset
        self.value = value
        self.length = 0

    def __repr__(self):
        return f"Token(offset={self.offset}, length={self.length}, value=0x{self.value:02X})"

class ScriptProcessor:
    def __init__(self, name: Optional[str] = None):
        self.info: Optional[ScriptInfo] = ScriptInfo.query_by_name(name) if name else None
        self.raw: bytes = b""
        self.tokens: List[Token] = []
        self.blocks: List[int] = []
        self.asmbin: bytes = b""
        self.asmbin_offset: int = 0
        self.version: Optional[int] = None

    def read(self, path: str, check: bool = True) -> 'ScriptProcessor':
        if not path:
            return self
        if check and not path.lower().endswith(".mes"):
            return self
        if not os.path.exists(path):
            return self
        with open(path, "rb") as f:
            self.raw = f.read()

        if len(self.raw) < 8:
            raise ValueError("Raw data is too short to contain a valid header.")
        head0, head1 = struct.unpack_from("<II", self.raw, 0)
        if head1 == 0x3:
            offset = head0 * 6 + 4
            block_count = (offset - 4) // 4
            if len(self.raw) >= 8:
                self.blocks = list(struct.unpack_from("<" + "I" * block_count, self.raw, 8))
            if len(self.raw) >= offset + 3:
                self.version = struct.unpack_from("<H", self.raw, offset)[0]
                if self.info is None:
                    self.info = ScriptInfo.query_by_version(self.version)
                self.asmbin_offset = offset + 3
                self.asmbin = self.raw[self.asmbin_offset:]
        else:
            offset = head0 * 4 + 4
            if len(self.raw) >= offset + 2:
                self.version = struct.unpack_from("<H", self.raw, offset)[0]
                if self.info is None:
                    self.info = ScriptInfo.query_by_version(self.version)
                self.asmbin_offset = offset + 2
                self.asmbin = self.raw[self.asmbin_offset:]
            if len(self.raw) >= 4:
                self.blocks = list(struct.unpack_from("<" + "I" * head0, self.raw, 4))

        self._token_parse()
        return self

    def _token_parse(self) -> None:
        offset = 0
        data = self.asmbin
        while offset < len(data):
            token = Token(offset, data[offset])
            val = token.value
            if self.info.uint8x2.its(val):
                token.length = 3
            elif self.info.uint8str.its(val):
                token.length = 2
                while True:
                    token.length += 1
                    if data[offset + token.length - 1] == 0:
                        break
            elif self.info.string.its(val) or self.info.encstr.its(val):
                token.length = 0
                while (offset + token.length) < len(data):
                    token.length += 1
                    if data[offset + token.length - 1] == 0:
                        break
            elif self.info.uint16x4.its(val):
                token.length = 9
            else:
                raise Exception("Error while parsing token at offset {}.".format(offset))
            self.tokens.append(token)
            offset += token.length

    def fetch_scene_text(self, absolute_file_offset: bool = True) -> List[Dict[str, Any]]:
        result = []
        base = self.asmbin_offset if absolute_file_offset else 0
        data = self.asmbin

        for token in self.tokens:
            if self.info.string.its(token.value):
                raw_text = data[token.offset : token.offset + token.length]
                param = raw_text[0]
                text = raw_text[1:]
                text = text.split(b'\0')[0].decode('cp932')
                result.append({"offset": token.offset + base, "type": "string", "param": param, "string": text})

            elif self.info.encstr.its(token.value):
                raw_text = data[token.offset : token.offset + token.length]
                param = raw_text[0]
                text = raw_text[1:]
                # 解密处理：对每个非零字节加 0x20 后取低8位
                text = bytes((b + 0x20) & 0xFF for b in text if b != 0)
                text = text.split(b'\0')[0].decode('cp932')
                result.append({"offset": token.offset + base, "type": "encstr", "param": param, "string": text})

        return result

    def is_parsed(self) -> bool:
        return self.asmbin != b"" and len(self.tokens) > 0

if __name__ == "__main__":
    mes_dir = r"D:\GAL\2009年3月\Princess Party\AdvData\MES"
    version = 0
    result = []
    seen = set()
    for file in os.listdir(mes_dir):
        if file.endswith(".mes") or file.endswith(".MES"):
            file_path = os.path.join(mes_dir, file)
            print(file_path)
            processor = ScriptProcessor()
            processor.read(file_path)
            if processor.is_parsed():
                texts = processor.fetch_scene_text()
                is_VOICE = False
                is_SPEAKER = False

                match version:
                    case 0:
                        for text in texts:
                            if not is_VOICE and not is_SPEAKER and text['type'] == "string" and text['param'] == 55:
                                is_VOICE = True
                                is_SPEAKER = False
                                tmp_voice = text['string']
                                if not tmp_voice.endswith('.wav') and not tmp_voice.endswith('.ogg'):
                                    tmp_voice = tmp_voice + '.wav'
                                
                            elif is_VOICE and not is_SPEAKER and text["type"] == "encstr" and 70 <= text["param"] <= 80:
                                is_VOICE = False
                                is_SPEAKER = True
                                tmp_speaker = text["string"]
                                param1 = text["param"]
                            elif not is_VOICE and is_SPEAKER and text["type"] == "encstr" and text["param"] == param1 + 1:
                                is_VOICE = False
                                is_SPEAKER = False
                                tmp_text = text["string"]
                                tmp_text = tmp_text.replace("\n", "").replace('\u3000', '').replace('$n', '')
                                tmp_text = tmp_text.replace('『', '').replace('』', '').replace('「', '').replace('」', '')
                                tmp_text = tmp_text.replace('（', '').replace('）', '')
                                tmp_text = re.sub(r'｛[^／]+／([^｝]+)｝', r'\1', tmp_text)
                                if (tmp_speaker != '？？？' and tmp_speaker != '$n' and tmp_voice not in seen and '○' not in tmp_text):
                                    seen.add(tmp_voice)
                                    result.append({"Speaker": tmp_speaker, "Voice": tmp_voice, "Text": tmp_text})
                            else:
                                is_VOICE = False
                                is_SPEAKER = False
                                tmp_voice = ""
                                tmp_speaker = ""
                                tmp_text = ""
                    case 1:
                        for text in texts:
                            if text["type"] == "string" and text["param"] == 77:
                                continue
                            if not is_VOICE and not is_SPEAKER and text['type'] == "string" and text['param'] == 76:
                                is_VOICE = True
                                is_SPEAKER = False
                                tmp_voice = text['string']
                                if not tmp_voice.endswith('.wav') and not tmp_voice.endswith('.ogg'):
                                    tmp_voice = tmp_voice + '.ogg'
                                tmp_voice = tmp_voice.replace(".wav", ".ogg")
                                
                            elif is_VOICE and not is_SPEAKER and text["type"] == "encstr" and text["param"] == 105:
                                is_VOICE = False
                                is_SPEAKER = True
                                tmp_speaker = text["string"]
                                param1 = text["param"]
                            elif not is_VOICE and is_SPEAKER and text["type"] == "encstr" and text["param"] == param1 + 1:
                                is_VOICE = False
                                is_SPEAKER = False
                                tmp_text = text["string"]
                                tmp_text = tmp_text.replace("\n", "").replace('\u3000', '').replace('$n', '')
                                tmp_text = tmp_text.replace('『', '').replace('』', '').replace('「', '').replace('」', '')
                                tmp_text = tmp_text.replace('（', '').replace('）', '')
                                tmp_text = re.sub(r'｛[^／]+／([^｝]+)｝', r'\1', tmp_text)
                                tmp_text = re.sub(r'@[a-z0-9]+', '', tmp_text)
                                if (tmp_speaker != '？？？' and tmp_speaker != '$n' and tmp_voice not in seen and '○' not in tmp_text):
                                    seen.add(tmp_voice)
                                    result.append({"Speaker": tmp_speaker, "Voice": tmp_voice, "Text": tmp_text})
                            else:
                                is_VOICE = False
                                is_SPEAKER = False
                                tmp_voice = ""
                                tmp_speaker = ""
                                tmp_text = ""

    with open(r"D:\Fuck_galgame\index.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)