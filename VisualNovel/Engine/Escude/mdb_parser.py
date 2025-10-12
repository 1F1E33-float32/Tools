from __future__ import annotations

import os
import struct
from typing import Any, List, Optional, Tuple

MAGIC = 0x0062646D  # little-endian: b"mdb\x00"


def parse_mdb_bin(path: str, enc: str = "cp932"):
    """
    Parse a MDB binary file.

    Returns a list of (sheet_name, rows) tuples where each row is a list of cell values.

    Based on C code structure:
        u32 magic (0x0062646d)
        while not sentinel:
            u32 sheet_size
            SHEET {
                u32 name;      // offset into text pool
                u32 cols;      // number of columns
                struct COL {
                    u16 type;  // 4 = string, 2 = float, others = numeric
                    u16 size;  // size in bytes
                    u32 name;  // offset into text pool
                } col[];
            }
            u32 data_size
            u8[] data       // row data
            u32 text_size
            u8[] text       // string pool

    Parameters
    ----------
    path : str
        File path to the binary DB.
    enc : str
        Encoding for text pool (default 'cp932' for Shift-JIS Japanese).
    """
    with open(path, "rb") as f:
        buf = f.read()

    def ru32(o: int) -> int:
        return struct.unpack_from("<I", buf, o)[0]

    def cstr(pool: bytes, pos: int) -> str:
        if pos >= len(pool):
            return ""
        e = pool.find(b"\x00", pos)
        e = len(pool) if e < 0 else e
        return pool[pos:e].decode(enc, errors="replace")

    off = 0
    if ru32(off) != MAGIC:
        return []
    off += 4

    out = []

    while True:
        if off + 4 > len(buf):
            break
        hsz = ru32(off)
        off += 4
        if hsz == 0:
            break

        # Read SHEET header
        hdr = buf[off : off + hsz]
        off += hsz

        # Read data blob
        dsz = ru32(off)
        off += 4
        data = buf[off : off + dsz]
        off += dsz

        # Read text pool
        tsz = ru32(off)
        off += 4
        text = buf[off : off + tsz]
        off += tsz

        # Parse SHEET header
        ho = 0
        name_off = struct.unpack_from("<I", hdr, ho)[0]
        ho += 4
        cols = struct.unpack_from("<I", hdr, ho)[0]
        ho += 4

        # Read column metadata
        col_sizes: List[int] = []
        col_names: List[str] = []
        col_types: List[int] = []
        for _ in range(cols):
            ctype = struct.unpack_from("<H", hdr, ho)[0]
            csize = struct.unpack_from("<H", hdr, ho + 2)[0]
            coff = struct.unpack_from("<I", hdr, ho + 4)[0]
            ho += 8
            col_types.append(ctype)
            col_sizes.append(csize)
            col_names.append(cstr(text, coff))

        sheet_name = cstr(text, name_off)
        stride = sum(col_sizes)

        # Parse rows
        rows: List[List[Any]] = []
        if stride > 0 and dsz >= stride:
            rc = dsz // stride
            p = 0
            for _ in range(rc):
                row: List[Any] = []
                cp = 0
                for k in range(cols):
                    field = data[p + cp : p + cp + col_sizes[k]]
                    if col_types[k] == 4 and len(field) >= 4:
                        # String type - offset into text pool
                        off2 = struct.unpack_from("<I", field, 0)[0]
                        row.append(cstr(text, off2))
                    elif col_sizes[k] == 4 and col_types[k] == 2:
                        # Float type
                        row.append(struct.unpack_from("<f", field, 0)[0])
                    elif col_sizes[k] == 4:
                        # Signed int32
                        row.append(struct.unpack_from("<i", field, 0)[0])
                    elif col_sizes[k] == 2:
                        # Signed int16
                        row.append(struct.unpack_from("<h", field, 0)[0])
                    elif col_sizes[k] == 1:
                        # Signed int8
                        row.append(struct.unpack_from("<b", field, 0)[0])
                    else:
                        # Fallback: hex string
                        row.append(field.hex())
                    cp += col_sizes[k]
                rows.append(row)
                p += stride

        out.append((sheet_name, rows))

    return out


def load_name_table(db_scripts_path):
    if not db_scripts_path or not os.path.isfile(db_scripts_path):
        return None

    sheets = parse_mdb_bin(db_scripts_path, enc="cp932")
    name_rows: Optional[List[List[Any]]] = None

    for nm, rows in sheets:
        if nm and (nm == "登場人物" or "登場人物" in nm or nm.lower().startswith("name")):
            name_rows = rows
            break

    if not name_rows:
        return None

    # First column is display name string
    table = [(r[0] if len(r) > 0 and isinstance(r[0], str) else "") for r in name_rows]
    return table


def load_voice_table(db_scripts_path):
    if not db_scripts_path or not os.path.isfile(db_scripts_path):
        return None

    sheets = parse_mdb_bin(db_scripts_path, enc="cp932")

    for sheet_name, rows in sheets:
        # '音声' sheet
        if sheet_name and (sheet_name == "音声" or "音声" in sheet_name or sheet_name.lower().startswith("voice")):
            # Columns: 識別子(name), サブフォルダ(path), 音声グループ(group), サンプル音声(sample_id), サンプル音声数
            out: List[Tuple[str, str, int]] = []
            for row in rows:
                name = row[0] if len(row) > 0 and isinstance(row[0], str) else ""
                path = row[1] if len(row) > 1 and isinstance(row[1], str) else ""
                group = row[2] if len(row) > 2 and isinstance(row[2], int) else 0
                out.append((name, path, group))
            return out

    return None
