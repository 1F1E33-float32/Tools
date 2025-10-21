from typing import Any, Dict, List, Tuple


def ArchiveInfo_GetPackageNameFromBodyBin(file_name: str) -> str:
    if not file_name:
        return ""
    if "_body." in file_name:
        return file_name.split("_body.")[0]
    if "body." in file_name:
        return file_name.split("body.")[0]
    return ""


def ArchiveInfo_GetAllPossibleFileNames(name: str, suffix: str, keepDirectory: bool = False) -> List[str]:
    if not name:
        return []
    res = [name + suffix, name]
    return list(dict.fromkeys(res))


def ArchiveInfo_GetItemPositionFromRangeList(range_obj: Any, archive_info_type: Any = None) -> Tuple[int, int]:
    return 0, 0


def ArchiveInfo_GetLengthFromRangeList(range_obj: Any, archive_info_type: Any = None) -> int:
    return 0


def get_root_key(t: Any) -> str | None:
    if int(getattr(t, "value", int(t))) == 1:
        return "file_info"
    if int(getattr(t, "value", int(t))) == 2:
        return "umd_root"
    return None


class PsbExtension:
    @staticmethod
    def MdfConvert(stream: Any, shell_type: str, context: Dict[str, Any]):
        raise ValueError("InvalidData")
