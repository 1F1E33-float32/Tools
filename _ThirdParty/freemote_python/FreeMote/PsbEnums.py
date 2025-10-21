from enum import Enum


class PsbType(Enum):
    PSB = 0
    Pimg = 1
    Scn = 2
    Mmo = 3
    Tachie = 4
    ArchiveInfo = 5
    BmpFont = 6
    Motion = 7
    SoundArchive = 8
    Map = 9
    SprBlock = 10
    SprData = 11
    ClutImg = 12
    Chip = 13
    Mpd = 14


class PsbSpec(Enum):
    none = -128
    common = 0
    krkr = 1
    win = 2
    ems = 3
    psp = 4
    vita = 5
    ps4 = 6
    nx = 7
    citra = 8
    and_ = 9
    x360 = 10
    revo = 11
    other = 127


class PsbImageFormat(Enum):
    png = 0
    bmp = 1


class PsbExtractOption(Enum):
    Original = 0
    Extract = 1


class PsbArchiveInfoType(Enum):
    None_ = 0
    FileInfo = 1
    UmdRoot = 2
