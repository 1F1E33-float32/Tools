import struct
from typing import Any, Dict, List


class _Header:
    def __init__(self) -> None:
        self.Version = 3
        self.OffsetNames = 0
        self.OffsetEntries = 0
        self.OffsetStrings = 0
        self.OffsetStringsData = 0
        self.OffsetChunkOffsets = 0
        self.OffsetChunkLengths = 0
        self.OffsetChunkData = 0


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.p = 0

    def seek(self, pos: int) -> None:
        self.p = pos

    def read(self, n: int) -> bytes:
        b = self.data[self.p : self.p + n]
        self.p += n
        return b

    def read_u32(self) -> int:
        v = struct.unpack_from("<I", self.data, self.p)[0]
        self.p += 4
        return v


def _unzip_uint(b: bytes) -> int:
    v = 0
    for i in range(min(len(b), 4)):
        v |= b[i] << (8 * i)
    return v


def _read_compact_uint(r: _Reader, size: int) -> int:
    return _unzip_uint(r.read(size))


def _read_psb_array(r: _Reader, n: int) -> List[int]:
    count = _read_compact_uint(r, n)
    entry_len = r.read(1)[0] - 0x0C
    total = entry_len * count if count >= 0 else 0
    raw = r.read(total) if total > 0 else b""
    res: List[int] = []
    for i in range(count):
        start = i * entry_len
        val = _unzip_uint(raw[start : start + entry_len])
        res.append(val)
    return res


def _read_number(r: _Reader, t: int) -> Any:
    if t == 0x04:
        return 0
    if 0x05 <= t <= 0x0C:
        size = t - 0x05 + 1
        b = r.read(size)
        signed = (b[-1] & 0x80) != 0
        b = b + ((b"\xff" if signed else b"\x00") * (8 - len(b)))
        return int.from_bytes(b, "little", signed=True)
    if t == 0x1D:
        return 0.0
    if t == 0x1E:
        b = r.read(4)
        return struct.unpack("<f", b)[0]
    if t == 0x1F:
        b = r.read(8)
        return struct.unpack("<d", b)[0]
    return 0


class TypeHandler:
    def OutputResources(self, psb: "PSB", context: Any, name: str, dir_path: str, extract_option: Any) -> Dict[str, str]:
        return {}

    def UnlinkToFile(self, psb: "PSB", context: Any, name: str, dir_path: str, output_unlinked_psb: bool, order: Any) -> None:
        return None


class PSB:
    def __init__(self, path_or_stream: Any = None, *args, **kwargs) -> None:
        self.Type = None
        self.Root = {}
        self.Objects = {}
        self.Resources = []
        self.ExtraResources = []
        self.TypeHandler = TypeHandler()
        self.Platform = None
        self.Header = _Header()
        if isinstance(path_or_stream, (str, bytes)) or hasattr(path_or_stream, "read"):
            if isinstance(path_or_stream, str):
                with open(path_or_stream, "rb") as f:
                    data = f.read()
            elif hasattr(path_or_stream, "read"):
                data = path_or_stream.read()
            else:
                data = path_or_stream
            self._load_from_bytes(data)

    @staticmethod
    def DullahanLoad(stream: Any) -> "PSB":
        if hasattr(stream, "read"):
            data = stream.read()
        else:
            data = bytes(stream)
        return PSB(data)

    def _load_from_bytes(self, data: bytes) -> None:
        r = _Reader(data)
        if data[:4] != b"PSB\x00":
            raise ValueError("Not PSB")
        r.seek(4)
        self.Header.Version = r.read_u32()
        offs = [r.read_u32() for _ in range(10)]
        self.Header.OffsetNames = offs[0]
        self.Header.OffsetStrings = offs[2]
        self.Header.OffsetStringsData = offs[3]
        self.Header.OffsetChunkOffsets = offs[4]
        self.Header.OffsetChunkLengths = offs[5]
        self.Header.OffsetChunkData = offs[6]
        self.Header.OffsetEntries = offs[7]
        r.seek(self.Header.OffsetStrings)
        n_type = r.read(1)[0]
        self._string_offsets = _read_psb_array(r, n_type - 0x0D + 1)
        r.seek(self.Header.OffsetNames)
        n1 = r.read(1)[0]
        charset = _read_psb_array(r, n1 - 0x0D + 1)
        n2_type = r.read(1)[0]
        names_data = _read_psb_array(r, n2_type - 0x0D + 1)
        n3_type = r.read(1)[0]
        name_indexes = _read_psb_array(r, n3_type - 0x0D + 1)
        names: List[str] = []
        for idx in name_indexes:
            cur = names_data[idx]
            buf: List[int] = []
            while cur != 0:
                code = names_data[cur]
                d = charset[code]
                real_chr = cur - d
                cur = code
                buf.append(real_chr & 0xFF)
            buf.reverse()
            names.append(bytes(buf).decode("utf-8", errors="ignore"))
        self.Names = names
        r.seek(self.Header.OffsetEntries)
        self.Root = self._unpack(r)
        if isinstance(self.Root, dict):
            self.Objects = self.Root

    def _read_string_by_index(self, idx: int, r: _Reader) -> str:
        if idx < 0 or idx >= len(self._string_offsets):
            return ""
        start = self.Header.OffsetStringsData + self._string_offsets[idx]
        end = start
        data = r.data
        while end < len(data) and data[end] != 0:
            end += 1
        return data[start:end].decode("utf-8", errors="ignore")

    def _unpack(self, r: _Reader) -> Any:
        t = r.read(1)[0]
        if t == 0x00:
            return None
        if t == 0x01:
            return None
        if t == 0x02:
            return False
        if t == 0x03:
            return True
        if 0x04 <= t <= 0x0C or 0x1D <= t <= 0x1F:
            return _read_number(r, t)
        if 0x0D <= t <= 0x14:
            n = t - 0x0D + 1
            return _read_psb_array(r, n)
        if 0x15 <= t <= 0x18:
            n = t - 0x15 + 1
            idx = _read_compact_uint(r, n)
            return self._read_string_by_index(idx, r)
        if 0x19 <= t <= 0x1C or 0x22 <= t <= 0x25:
            n = (t - 0x19 + 1) if t <= 0x1C else (t - 0x22 + 1)
            idx = _read_compact_uint(r, n)
            return {"$res": int(idx)}
        if t == 0x20:
            n_type = r.read(1)[0]
            n = n_type - 0x0D + 1
            offsets = _read_psb_array(r, n)
            pos = r.p
            res_list: List[Any] = []
            for off in offsets:
                r.seek(pos + off)
                res_list.append(self._unpack(r))
            r.seek(pos + (offsets[-1] if offsets else 0))
            return res_list
        if t == 0x21:
            n_names_type = r.read(1)[0]
            n1 = n_names_type - 0x0D + 1
            names_idx = _read_psb_array(r, n1)
            n_off_type = r.read(1)[0]
            n2 = n_off_type - 0x0D + 1
            offsets = _read_psb_array(r, n2)
            pos = r.p
            d: Dict[str, Any] = {}
            for i, off in enumerate(offsets):
                r.seek(pos + off)
                key_name = self.Names[names_idx[i]] if i < len(names_idx) else str(i)
                d[key_name] = self._unpack(r)
            r.seek(pos + (offsets[-1] if offsets else 0))
            return d
        return None
