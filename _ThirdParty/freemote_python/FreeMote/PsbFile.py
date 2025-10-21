from typing import Any


class PsbFile:
    @staticmethod
    def GetSignatureShellType(stream: Any) -> str | None:
        pos = stream.tell()
        header = stream.read(4)
        stream.seek(pos)
        if len(header) < 4:
            return None
        if header[0:4] == b"PSB\x00":
            return "PSB"
        if header[0:3] == b"mdf" and header[3] == 0:
            return "MDF"
        if header[0:3] == b"mfl" and header[3] == 0:
            return "MFL"
        if header[0:3] == b"mzs" and header[3] == 0:
            return "MZS"
        if header[0:3] == b"mxb" and header[3] == 0:
            return "MXB"
        return None

    @staticmethod
    def Encode(key: int, mode: Any, pos: Any, stream: Any, out_stream: Any) -> None:
        pass
