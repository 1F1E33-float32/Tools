# Reference: https://github.com/luoyily/SoftPal-Tool/blob/main/pal_script_tool.py

import argparse
import json
import os
import re
import struct
from dataclasses import dataclass
from typing import Optional


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--JA", type=str, default=r"D:\Fuck_VN")
    parser.add_argument("--op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args()


def text_cleaning(text):
    text = re.sub(r"<.*?>|%\d+", "", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "")
    text = text.replace("（", "").replace("）", "").replace("　", "")
    return text


def dword_to_int(dword: bytes) -> int:
    return struct.unpack("I", dword)[0]


@dataclass
class TextItem:
    offset: int
    index: bytes
    text: str


@dataclass
class FileItem:
    index: int
    name: str


@dataclass
class ScriptItem:
    offset: int
    text_offset: int
    name_offset: Optional[int] = None
    voice_index: Optional[int] = None
    has_name: bool = False
    has_voice: bool = False
    type: str = "textshow"


class ScriptDisassembler:
    def __init__(self, script_src_file, text_dat_file, file_dat_file, mix_dir):
        with open(script_src_file, "rb") as f:
            self.SCRIPT_SRC = f.read()
        with open(text_dat_file, "rb") as f:
            self.TEXT_DAT = f.read()
        with open(file_dat_file, "rb") as f:
            self.FILE_DAT = f.read()

        self.text_items, self.offset_to_text_idx = self._parse_text_dat(self.TEXT_DAT)
        self.file_items = self._parse_file_dat(self.FILE_DAT)
        self.mix_index = self._parse_mix_dir(mix_dir)

        self.script_items = []
        self.script_offset_map = {}

    @staticmethod
    def _parse_text_dat(data):
        items = []
        offset_to_idx = {}
        idx = 0
        off = 0x10
        while off < len(data):
            end = data.find(b"\x00", off + 4)
            if end < 0:
                break
            chunk = data[off:end]
            if len(chunk) < 4:
                break
            index_bytes = chunk[:4]
            try:
                txt = chunk[4:].decode("cp932", errors="ignore")
            except Exception:
                txt = ""
            items.append(TextItem(offset=off, index=index_bytes, text=txt))
            offset_to_idx[off] = idx
            idx += 1
            off = end + 1
        return items, offset_to_idx

    @staticmethod
    def _parse_file_dat(data):
        files = []
        for i, off in enumerate(range(0x10, len(data), 0x20)):
            entry = data[off : off + 0x20]
            z = entry.find(b"\x00")
            name = (entry[:z] if z != -1 else entry).decode("cp932", errors="ignore")
            files.append(FileItem(index=i, name=name))
        return files

    @staticmethod
    def _parse_mix_file(path):
        voices = []
        with open(path, "rb") as f:
            data = f.read()
        for off in range(0, len(data), 0x20):
            chunk = data[off : off + 0x20]
            if not chunk or chunk[0] == 0:
                continue
            s = chunk.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
            s = s.strip()
            if s:
                voices.append(s.upper())
        return voices

    def _parse_mix_dir(self, mix_dir):
        idx = {}
        if not mix_dir or not os.path.isdir(mix_dir):
            return idx
        for fname in os.listdir(mix_dir):
            if fname.lower().endswith(".mix"):
                base = os.path.splitext(fname)[0].upper()
                path = os.path.join(mix_dir, fname)
                voices = self._parse_mix_file(path)
                if voices:
                    idx[base] = voices
        return idx

    def parse_script_data(self):
        n = 0
        src = self.SCRIPT_SRC
        for i in range(0, len(src) - 4, 4):
            if src[i : i + 4] == b"\x17\x00\x01\x00":
                hi = src[i + 6 : i + 8]
                lo = src[i + 4 : i + 6]
                txt_types = {b"\x02\x00", b"\x0f\x00", b"\x10\x00", b"\x11\x00", b"\x12\x00", b"\x13\x00", b"\x14\x00"} # 这里的opcode不全，需要进一步逆向
                if hi == b"\x02\x00" and lo in txt_types:
                    start = i - 24
                    if start < 0:
                        continue
                    chunk = src[start : i + 8]
                    itm = self._make_item(chunk, start, "textshow")
                elif hi == b"\x06\x00" and lo == b"\x02\x00":
                    start = i - 8
                    if start < 0:
                        continue
                    chunk = src[start : i + 8]
                    itm = self._make_item(chunk, start, "select")
                else:
                    continue
                self.script_items.append(itm)
                self.script_offset_map[start] = n
                n += 1

    @staticmethod
    def _make_item(chunk, offset, typ):
        text_off = dword_to_int(chunk[4:8])
        if typ == "textshow":
            name_off = dword_to_int(chunk[12:16])
            voice_idx = dword_to_int(chunk[20:24])
            return ScriptItem(
                offset=offset,
                text_offset=text_off,
                name_offset=name_off,
                voice_index=voice_idx,
                has_name=(chunk[12:16] != b"\xff\xff\xff\x0f"),
                has_voice=(chunk[20:24] != b"\xff\xff\xff\x0f"),
                type=typ,
            )
        else:  # select
            return ScriptItem(offset=offset, text_offset=text_off, type=typ)

    def _find_text(self, offset):
        idx = self.offset_to_text_idx.get(offset)
        return self.text_items[idx] if idx is not None else None

    def export_json(self, path):
        out = []

        for s in self.script_items:
            name_txt = None
            voice_code = None
            text_item = self._find_text(s.text_offset)
            if not text_item:
                print(f"[WARN] Text offset 0x{s.text_offset:X} not found, skipped")
                continue

            text_clean = text_cleaning(text_item.text)

            if s.has_name:
                name_item = self._find_text(s.name_offset)
                if not name_item:
                    print(f"[WARN] Name offset 0x{s.name_offset:X} not found, skipped")
                    continue
                name_txt = name_item.text

            if s.type == "textshow" and s.has_voice:
                if s.voice_index is not None and s.voice_index < len(self.file_items):
                    voice_code = self.file_items[s.voice_index].name
                else:
                    print(f"[WARN] Voice index {s.voice_index} out of range, skipped")
                    continue

            expanded = False
            if voice_code and (voice_key := voice_code.upper()) in self.mix_index and name_txt:
                speakers = [p.strip() for p in name_txt.split("・") if p.strip()]
                voices = self.mix_index[voice_key]
                if len(speakers) == 0 or len(voices) == 0:
                    pass
                else:
                    expanded = True
                    for spk, vc in zip(speakers, voices):
                        out.append({"Speaker": spk, "Voice": vc.upper(), "Text": text_clean})

            if not expanded and voice_code and name_txt:
                out.append({"Speaker": name_txt, "Voice": voice_code.upper(), "Text": text_clean})

        seen = set()
        unique_results = []
        for entry in out:
            v = entry.get("Voice")
            if v and v not in seen:
                seen.add(v)
                unique_results.append(entry)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    dis = ScriptDisassembler(
        script_src_file=os.path.join(args.JA, "SCRIPT.SRC"),
        text_dat_file=os.path.join(args.JA, "TEXT.DAT"),
        file_dat_file=os.path.join(args.JA, "FILE.DAT"),
        mix_dir=os.path.join(args.JA),
    )
    dis.parse_script_data()
    dis.export_json(args.op)
