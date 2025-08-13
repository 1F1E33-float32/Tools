#!/usr/bin/env python3
import os
import struct
from io import BytesIO

def dec_str(bs: bytes) -> str:
    """XOR‐decode a byte sequence with 0x53 and decode as CP932."""
    b2 = bytes(b ^ 0x53 for b in bs)
    return b2.decode('cp932', errors='replace')

def ext_bin(data: bytes) -> str:
    stm = BytesIO(data)
    # header: skip, then fun1_len, fun2_len, fun3_len, code_len, res_len
    fun1_len, fun2_len, fun3_len, code_len, res_len = struct.unpack(
        '<12xI4xI4xIII', stm.read(0x28)
    )

    # skip over tables + padding + two ints
    stm.seek(fun1_len + fun2_len + fun3_len + 0x28 + 8)
    res_off = stm.tell() + code_len + 2

    out_lines = []
    while stm.tell() < res_off - 2:
        op, count, unk1, unk2 = struct.unpack('<Hhhh', stm.read(8))
        # TEXT BOX
        if op == 1:
            num_strs = unk1
            # first Arg → could be voice code
            a_type, a_len, a_off = struct.unpack('<HHI', stm.read(8))
            str_idx = voice_idx = None
            if a_type == 5:
                # this is a string like 'v0000#0001'
                raw = data[res_off + a_off: res_off + a_off + a_len]
                code_str = dec_str(raw)
                # split into text index and voice index
                if '#' in code_str:
                    parts = code_str.lstrip('v').split('#', 1)
                    str_idx, voice_idx = parts[0], parts[1]
            elif a_type == 4:
                val = a_off
                str_idx   = str(val & 0xFFFF)
                voice_idx = str(val >> 16)
            elif a_type == 3:
                buf = data[res_off + a_off: res_off + a_off + 8]
                idx0, idx1 = struct.unpack('<II', buf)
                str_idx, voice_idx = str(idx0), str(idx1)

            # read actual strings
            texts = []
            for _ in range(num_strs):
                t, length, offset = struct.unpack('<HHI', stm.read(8))
                if t != 5:
                    raise ValueError(f"Expected string arg, got type {t}")
                raw = data[res_off + offset: res_off + offset + length]
                texts.append(dec_str(raw))

            header = f"[idx:{str_idx}, voice:{voice_idx}]"
            out_lines.append(header + " " + "\n".join(texts))

        # NAME + TEXT BOX
        elif op == 0x3C:
            num_strs = unk1
            a_type, a_len, a_off = struct.unpack('<HHI', stm.read(8))
            str_idx = voice_idx = None
            if a_type == 5:
                raw = data[res_off + a_off: res_off + a_off + a_len]
                code_str = dec_str(raw)
                if '#' in code_str:
                    parts = code_str.lstrip('v').split('#', 1)
                    str_idx, voice_idx = parts[0], parts[1]
            elif a_type == 4:
                val = a_off
                str_idx   = str(val & 0xFFFF)
                voice_idx = str(val >> 16)
            elif a_type == 3:
                buf = data[res_off + a_off: res_off + a_off + 8]
                idx0, idx1 = struct.unpack('<II', buf)
                str_idx, voice_idx = str(idx0), str(idx1)

            # speaker name
            t2, l2, o2 = struct.unpack('<HHI', stm.read(8))
            if t2 != 5:
                raise ValueError(f"Expected name string, got type {t2}")
            raw_name = data[res_off + o2: res_off + o2 + l2]
            name = dec_str(raw_name)

            # remaining texts
            texts = []
            for _ in range(num_strs - 1):
                t, length, offset = struct.unpack('<HHI', stm.read(8))
                if t != 5:
                    raise ValueError(f"Expected string arg, got type {t}")
                raw = data[res_off + offset: res_off + offset + length]
                texts.append(dec_str(raw))

            header = f"{name}@[idx:{str_idx}, voice:{voice_idx}]"
            out_lines.append(header + "\n" + "\n".join(texts))

        # CHOICE MENU
        elif op == 0x64:
            if count != unk1:
                raise ValueError("Choice count mismatch")
            for _ in range(unk1):
                t, length, offset = struct.unpack('<HHI', stm.read(8))
                if t != 5:
                    raise ValueError(f"Expected string arg, got type {t}")
                raw = data[res_off + offset: res_off + offset + length]
                out_lines.append(dec_str(raw))

        # OTHER OPS: skip args
        else:
            if not (2 <= op <= 9) and count >= 0:
                stm.seek(count * 8, os.SEEK_CUR)
            elif count < 0:
                stm.seek(8, os.SEEK_CUR)

    return "\r\n".join(out_lines)


def process_all(
    rio_dir=r'D:\GAL\2010_01\Kikouyoku Senki Tenkuu no Yumina FD  -ForeverDreams-\DATA\rio',
    out_dir=r'D:\GAL\2010_01\Kikouyoku Senki Tenkuu no Yumina FD  -ForeverDreams-\DATA\riotxt'
):
    os.makedirs(out_dir, exist_ok=True)

    for fname in os.listdir(rio_dir):
        if not fname.lower().endswith('.bin'):
            continue

        in_path  = os.path.join(rio_dir, fname)
        out_path = os.path.join(out_dir, fname[:-4] + '.txt')

        with open(in_path, 'rb') as f:
            data = f.read()

        txt = ext_bin(data)
        if not txt:
            continue

        # write using UTF-8
        with open(out_path, 'w', encoding='utf-8', errors='replace') as fo:
            fo.write(txt)

if __name__ == '__main__':
    process_all()
