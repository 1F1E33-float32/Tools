import strfile
import os
import json
import argparse
from struct import unpack

def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=r"D:\\Fuck_galgame\\script")
    parser.add_argument("--output", type=str, default=r"D:\\Fuck_galgame\\index.json")
    return parser.parse_args()


def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace('／', '').replace('\n', '')
    return text


def decStr(astr):
    a = ""
    for i in astr:
        a += chr(i ^ 0x53)
    return a


def _decode_cp932_from_raw(s):
    return s.encode("raw-unicode-escape").decode("932", errors="replace")


def split_voice_idx(idx):
    tail = idx % 100000
    pack_num, nth0 = divmod(tail - 1, 256)
    return f"v{pack_num:04d}", f"{nth0 + 1:04d}"


def extBin(stm):
    fun1_len, fun2_len, fun3_len, code_len, res_len = unpack("12xI4xI4xIII", stm.read(0x28))
    stm.seek(fun1_len + fun2_len + fun3_len + 0x28 + 4 * 2)
    res_off = stm.tell() + code_len + 2
    results = []
    while stm.tell() < res_off - 2:
        op, count, mne1, mne2 = unpack("Hhhh", stm.read(8))
        if op == 1:
            if count - mne1 != 1:
                continue
            # 读取并解析 arg1：编号 与 声音 idx
            arg_type1, len1_1, off1 = unpack("HHI", stm.read(8))
            _num_id = -1
            voice_idx = -1
            if arg_type1 == 3:
                _num_id, voice_idx = unpack("II", stm[res_off + off1 : res_off + off1 + 8])
            elif arg_type1 == 4:
                _num_id = off1
            text_parts = []
            for j in range(mne1):
                arg_type, len1, off = unpack("HHI", stm.read(8))
                if arg_type != 5:
                    continue
                raw = decStr(stm[res_off + off : res_off + off + len1])
                text_parts.append(_decode_cp932_from_raw(raw))
            text = "".join(text_parts).strip()
            voice = None
            if voice_idx != -1:
                pack_name, nth = split_voice_idx(voice_idx)
                voice = f"{pack_name}_{nth}"
            if text:
                results.append({
                    "Speaker": "？？？",
                    "Voice":   voice,
                    "Text":    text,
                })
        elif op == 0x3C:
            if count - mne1 != 1 or count < 2:
                continue
            # 读取并解析 arg1：编号 与 声音 idx
            arg_type1, len1_1, off1 = unpack("HHI", stm.read(8))
            _num_id = -1
            voice_idx = -1
            if arg_type1 == 3:
                _num_id, voice_idx = unpack("II", stm[res_off + off1 : res_off + off1 + 8])
            elif arg_type1 == 4:
                _num_id = off1
            arg_type, len1, off = unpack("HHI", stm.read(8))
            raw_name = decStr(stm[res_off + off : res_off + off + len1])
            name = _decode_cp932_from_raw(raw_name)
            text_parts = []
            for j in range(mne1 - 1):
                arg_type, len1, off = unpack("HHI", stm.read(8))
                if arg_type != 5:
                    continue
                raw = decStr(stm[res_off + off : res_off + off + len1])
                text_parts.append(_decode_cp932_from_raw(raw))
            text = "".join(text_parts)
            text = text_cleaning(text)
            pack_name, nth = split_voice_idx(voice_idx)
            voice = f"{pack_name}_{nth}"
            if text:
                results.append({
                    "Speaker": name,
                    "Voice":   voice,
                    "Text":    text,
                })
        elif op == 0x64:
            if count != mne1:
                continue
            # 跳过（丢弃）此类文本，但仍然正确前进指针
            for j in range(mne1):
                arg_type, len1, off = unpack("HHI", stm.read(8))
                # 仅消费参数，不输出
                if arg_type == 5:
                    _ = stm[res_off + off : res_off + off + len1]
        else:
            if op not in range(2, 9 + 1) and count >= 0:
                stm.seek(count * 8, 1)
            elif count < 0:
                stm.seek(8, 1)

    return results


if __name__ == "__main__":
    args = args_parser()
    input_dir = args.input
    output_path = args.output

    results = []
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    for binf in os.listdir(input_dir):
        if not binf.lower().endswith(".bin"):
            continue
        input_file_path = os.path.join(input_dir, binf)
        with open(input_file_path, "rb") as fs:
            stm = strfile.MyStr(fs.read())
        results.extend(extBin(stm))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Wrote {len(results)} entries to {output_path}")
