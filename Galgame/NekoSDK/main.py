import os
import struct
import json

MAGIC = b"NEKOSDK_ADVSCRIPT2\x00"

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('　', '').replace('\n', '').replace('\r', '')
    return text

def read_str(f):
    length_data = f.read(4)
    if len(length_data) < 4:
        raise EOFError("Unexpected EOF reading string length")
    (length,) = struct.unpack('<I', length_data)
    raw = f.read(length)
    return raw.decode('shift_jis', errors='replace')

def extract_file(in_path):
    results = []
    with open(in_path, 'rb') as f:
        if f.read(len(MAGIC)) != MAGIC:
            raise ValueError(f"Invalid magic in {in_path}")
        (qty,) = struct.unpack('<I', f.read(4))
        nodes = []
        for _ in range(qty):
            id, _type1, _ofs, opcode = struct.unpack('<IIII', f.read(16))
            f.read(128)
            (next_id,) = struct.unpack('<I', f.read(4))
            f.read(64)
            strs = [read_str(f) for _ in range(33)]
            nodes.append((id, opcode, next_id, strs))

    for item in nodes:
        if item[1] == 5:
            speaker = item[3][1].rstrip('\x00').replace(" ", "")
            text = text_cleaning(item[3][2].rstrip('\x00'))
            voice = item[3][3].rstrip('\x00').split("\\")[-1]
            results.append({"Speaker": speaker, "Voice": voice, "Text": text})
    return results

def main(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    all_entries = []
    for fname in os.listdir(input_dir):
        in_path = os.path.join(input_dir, fname)
        try:
            entries = extract_file(in_path)
            all_entries.extend(entries)
        except Exception as e:
            print(f"Skipping {fname}: {e}")

    index_path = os.path.join(output_dir, 'index.json')
    with open(index_path, 'w', encoding='utf-8') as jf:
        json.dump(all_entries, jf, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    in_dir = r"D:\Fuck_galgame\script"
    out_dir = r"D:\Fuck_galgame"
    main(in_dir, out_dir)