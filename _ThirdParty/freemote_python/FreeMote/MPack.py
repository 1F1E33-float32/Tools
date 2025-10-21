from typing import Tuple


def IsSignatureMPack(data: bytes) -> Tuple[bool, str]:
    if len(data) < 4:
        return False, ""
    if data[0:3] == b"mdf" and data[3] == 0:
        return True, "MDF"
    if data[0:3] == b"mfl" and data[3] == 0:
        return True, "MFL"
    if data[0:3] == b"mzs" and data[3] == 0:
        return True, "MZS"
    if data[0:3] == b"mxb" and data[3] == 0:
        return True, "MXB"
    return False, ""
