# -*- coding: utf-8 -*-
import os
import struct
import re
import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', default=r"D:\GAL\#DL\Midori no Umi\rld_dec")
    parser.add_argument('--cp', default='932', help='字符串解码使用的代码页 (默认: 936)')
    return parser.parse_args()

class ByteFile:
    """Operate bytes buffer as a file，仅保留脚本中用到的方法"""
    def __init__(self, src: bytes):
        self.pData = 0
        self.b = bytearray(src)

    def read(self, num: int = -1) -> bytearray:
        if num < 0:
            data = self.b[self.pData:]
            self.pData = len(self.b)
        else:
            data = self.b[self.pData:self.pData + num]
            self.pData += num
        return data

    def seek(self, offset: int, mode: int = 0):
        if mode == 1:
            offset += self.pData
        elif mode == 2:
            offset = len(self.b) - offset
        self.pData = max(0, min(offset, len(self.b)))

    def readstr(self) -> bytearray:
        end = self.b.find(b'\0', self.pData)
        if end == -1:
            start = self.pData
            self.pData = len(self.b)
            return self.b[start:]
        start = self.pData
        self.pData = end + 1
        return self.b[start:end]

    def readu32(self) -> int:
        chunk = self.b[self.pData:self.pData + 4]
        self.pData += 4
        if len(chunk) < 4:
            return 0
        return chunk[0] | (chunk[1] << 8) | (chunk[2] << 16) | (chunk[3] << 24)


def parse_cmd(cmd: int):
    op = cmd & 0xffff
    int_cnt = (cmd >> 16) & 0xff
    str_cnt = (cmd >> 24) & 0x0f
    unk = cmd >> 28
    return op, int_cnt, str_cnt, unk


def parse_name_table(lines: list[str]) -> dict[int, str]:
    """从 defChara.rld 中提取名称索引表"""
    pat = re.compile(r'(\d+),\d*,\d*,([^,]+),.*')
    names: dict[int, str] = {}
    for l in lines:
        m = pat.match(l)
        if m:
            names[int(m.group(1))] = m.group(2)
    return names


def is_half(s: bytes, cp: str) -> bool:
    """判断 s.decode(cp) 后是否全都是单字节字符"""
    try:
        decoded = s.decode(cp)
    except Exception:
        return False
    return len(decoded) == len(s)


def parse_rld_header(stm: ByteFile):
    magic, unk1, unk2, inst_cnt, unk3 = struct.unpack('<4sIIII', stm.read(20))
    tag = stm.readstr()
    stm.seek(0x114)
    return magic, unk1, unk2, inst_cnt, unk3, tag


def parse_rld(stm: ByteFile, name_table: dict[int, str], cp: str):
    """
    解析单个 .rld 文件，返回 (完整日志列表, 纯文本列表)
    纯文本列表即后续反编译使用的核心字符串
    """
    txt: list[str] = []
    pure_txt: list[str] = []

    magic, h1, h2, inst_cnt, h3, h_tag = parse_rld_header(stm)
    if magic != b'\0DLR':
        raise ValueError('不是合法的 RLD 文件')

    txt.append(f'magic:{magic}, unk1:{h1}, unk2:{h2}, inst_cnt:{inst_cnt}, unk3:{h3}, tag:{h_tag}')
    txt.append('')

    for _ in range(inst_cnt):
        op, int_cnt, str_cnt, unk = parse_cmd(stm.readu32())
        txt.append(f'op:{op}, int_cnt:{int_cnt}, str_cnt:{str_cnt}, unk:{unk}')

        ints = [stm.readu32() for _ in range(int_cnt)]
        txt.append('int: ' + ', '.join(map(str, ints)))

        strs = [stm.readstr() for _ in range(str_cnt)]
        for s in strs:
            txt.append(s.decode(cp, errors='ignore'))

        # 按 op 类型筛选“纯文本”
        if op == 28:
            idx = ints[0]
            if idx in name_table:
                pure_txt.append('$' + name_table[idx])
            for s in strs:
                if s not in (b'*', b'$noname$') and s and s.count(b',') < 2:
                    pure_txt.append(s.decode(cp, errors='ignore'))
        elif op == 21:
            for s in strs:
                if s not in (b'*', b'$noname$') and s and s.count(b',') < 2:
                    pure_txt.append(s.decode(cp, errors='ignore'))
        elif op == 48:
            pure_txt.append(strs[0].decode(cp, errors='ignore'))
        elif op in (191, 203):
            s0 = strs[0]
            if not is_half(s0, cp):
                pure_txt.append(s0.decode(cp, errors='ignore'))

    return txt, pure_txt


def ext_all_rld(input_dir: str, cp: str) -> dict[str, list[str]]:
    """
    批量解析目录下所有 .rld 文件，
    返回 { filename: pure_txt_list } 字典
    """
    # 1. 从 defChara.rld 构建名称表
    char_path = os.path.join(input_dir, 'defChara.rld')
    with open(char_path, 'rb') as f:
        stm = ByteFile(f.read())
    _, pure_txt0 = parse_rld(stm, {}, cp)
    name_table = parse_name_table(pure_txt0)

    # 2. 逐个解析并收集 pure_txt
    results: dict[str, list[str]] = {}
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith('.rld'):
            continue
        path = os.path.join(input_dir, fname)
        with open(path, 'rb') as f:
            stm = ByteFile(f.read())
        _, pure_txt = parse_rld(stm, name_table, cp)
        if pure_txt:
            results[fname] = pure_txt

    return results


if __name__ == '__main__':
    args = parse_args()
    all_texts = ext_all_rld(args.input_dir, args.cp)