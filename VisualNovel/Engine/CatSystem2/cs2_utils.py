import re
import struct


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, n):
        if self.pos + n > len(self.data):
            raise EOFError
        b = self.data[self.pos : self.pos + n]
        self.pos += n
        return b

    def read_byte(self):
        return self.read(1)[0]

    def read_int_le(self):
        return struct.unpack("<i", self.read(4))[0]

    def read_int32_le(self):
        return struct.unpack("<i", self.read(4))[0]

    def read_uint16_le(self):
        return struct.unpack("<H", self.read(2))[0]

    def read_varint(self):
        result = 0
        shift = 0
        while True:
            b = self.read_byte()
            result |= (b & 0x7F) << shift
            if b < 0x80:
                break
            shift += 7
            if shift >= 35:
                raise ValueError("varint too long")
        return result

    def read_string(self):
        n = self.read_varint()
        if n == 0:
            return ""
        return self.read(n).decode("utf-8")

    def read_terminated_string(self, encoding="shift_jis"):
        start = self.pos
        while self.pos < len(self.data) and self.data[self.pos] != 0:
            self.pos += 1
        s = self.data[start : self.pos].decode(encoding, errors="replace")
        if self.pos < len(self.data):
            self.pos += 1  # skip \x00
        return s


CS2_MAIN_OPCODES = {
    "debug_on",
    "debug_off",
    "next",
    "frameoff",
    "frameon",
    "keyskip",
    "wait",
    "bg",
    "cg",
    "eg",
    "fg",
    "fw",
    "pl",
    "md",
    "mpl",
    "fmpl",
    "epl",
    "bgm",
    "se",
    "pcm",
    "cam",
    "draw",
    "drawdef",
    "wipe",
    "wipe2",
    "wipe3",
    "wipedef",
    "raster",
    "particle",
    "select",
    "name",
    "str",
    "strcmp",
    "auto",
    "title",
    "place",
    "eyecatch",
    "date",
    "movie",
    "ptsel",
    "end_of_kaisou",
    "cgreg",
    "end",
    "mapsel",
    "particle2",
    "autocap",
    "staffroll",
    "bench",
    "time",
    "event",
    "scene",
    "fes",
    "fesnc",
    "fesjs",
    "fessel",
    "baseimg",
    "cgflag",
    "select2",
    "saveload",
    "blur",
    "mosaic",
    "rdraw",
    "rwipe",
    "rwipe2",
    "get",
    "view3d",
    "pg",
    "cm",
    "lt",
    "mt",
    "texture",
    "max",
    "min",
    "fog",
    "view",
    "tonetbl",
    "rand",
    "initialize_header",
    "fess",
    "mesdraw",
    "autoface",
    "autosave",
    "fex",
    "getfbit",
    "setfbit",
    "clearfbit",
    "select2cp",
    "view3dscale",
    "strn",
    "cache",
    "jumpstop",
    "fselect",
    "particle3",
    "novel",
    "undo",
    "sysbtn",
    "week",
    "thumbnail",
    "skipstop",
    "autostop",
    "forcemesdel",
    "voiceoff",
    "rwmos",
    "rfmos",
    "wbreak",
    "call",
    "return",
    "dic_reg",
    "auto_next",
    "log_clear",
    "dic_reset_apend",
    "dbgstr",
    "debug",
    "fesds",
    "callmestag",
    "dic_check_update",
    "js_call",
    "js",
    "jsjs",
    "bs_clear",
    "rpflip",
    "rcflip",
    "drama",
    "scenetitle",
    "steam",
    "cancellabel",
    "emoinfo_getinfo",
    "emoinfo_getoffset",
    "rs",
    "intmap",
    "py",
    "lua",
    "mestips",
}


_SPACES = (" ", "\t")


def cut_comment(text: str) -> str:
    if text is None:
        return ""
    idx = text.find("//")
    return text if idx < 0 else text[:idx]


def is_ascii_only_first(s: str) -> bool:
    for ch in s:
        if ch not in _SPACES:
            return ord(ch) < 0x80
    return True


def is_message_text(text: str) -> bool:
    if text is None:
        return False
    t = cut_comment(text)
    if t.strip() == "":
        return False
    first = t[0]
    flag = first in _SPACES
    parts = [p for p in re.split(r"[\t ]+", t) if p]
    n = len(parts)
    start = 0 if flag else 1
    text2 = None
    if n > start:
        text2 = "".join(parts[start:])

    if not flag:
        if text2 is not None:
            if parts[0] == "\\":
                return True
            if parts[0] == "$":
                return True
            try:
                int(parts[0])
                return True
            except Exception:
                pass
        return True

    if text2 is None:
        return False
    c0 = text2[0]
    if c0 in ("\\", "[", "$"):
        return True
    if c0 == "%":
        return False
    if not is_ascii_only_first(text2):
        return True
    return False


def extract_message(text: str):
    if text is None:
        return None
    raw = text
    t = cut_comment(text)
    trimmed = t.strip()
    if trimmed == "":
        return None
    flag = t[0] in _SPACES
    parts = [p for p in re.split(r"[\t ]+", t) if p]
    n = len(parts)
    start = 0 if flag else 1
    text2 = None
    if n > start:
        text2 = "".join(parts[start:])

    if not flag:
        if text2 is not None:
            if parts[0] == "\\":
                return {"name": None, "text": text2, "indexPrefix": None, "raw": raw, "trimmed": trimmed}
            if parts[0] == "$":
                return {"name": None, "text": text2, "indexPrefix": None, "raw": raw, "trimmed": trimmed}
            try:
                val = int(parts[0])
                return {"name": None, "text": text2, "indexPrefix": val, "raw": raw, "trimmed": trimmed}
            except Exception:
                pass
        if text2 is None:
            return {"name": parts[0], "text": None, "indexPrefix": None, "raw": raw, "trimmed": trimmed}
        return {"name": parts[0], "text": text2, "indexPrefix": None, "raw": raw, "trimmed": trimmed}

    if text2 is None:
        return None
    c0 = text2[0]
    if c0 in ("\\", "[", "$"):
        return {"name": None, "text": text2, "indexPrefix": None, "raw": raw, "trimmed": trimmed}
    if c0 == "%":
        return None
    if not is_ascii_only_first(text2):
        return {"name": None, "text": text2, "indexPrefix": None, "raw": raw, "trimmed": trimmed}
    return None


def is_command_line(text: str) -> bool:
    t = cut_comment(text)
    if t.strip() == "":
        return False
    return not is_message_text(t)


def tokenize_spaces(text: str):
    t = cut_comment(text).strip()
    if not t:
        return []
    return [p for p in re.split(r"[\t ]+", t) if p]


def parse_command_line(text: str):
    toks = tokenize_spaces(text)
    if not toks:
        return None
    return {"opcode": toks[0], "args": toks[1:], "raw": cut_comment(text).strip()}


def parse_lines_to_opcodes(lines, known_opcodes=None):
    out = []
    known = set(known_opcodes or [])
    for i, line in enumerate(lines):
        if is_command_line(line):
            item = parse_command_line(line)
            if item:
                item.update(
                    {
                        "index": i,
                        "is_known": (item["opcode"] in known) if known else None,
                    }
                )
                out.append(item)
    return out
