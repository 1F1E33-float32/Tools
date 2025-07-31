import os
import struct
import json
import argparse

MAGIC = b"NEKOSDK_ADVSCRIPT2\x00"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=r"D:\Fuck_galgame\script")
    parser.add_argument("--output-dir", default=r"D:\Fuck_galgame")
    return parser.parse_args()

def text_cleaning(text):
    text = text.replace('『', '').replace('』', '')
    text = text.replace('「', '').replace('」', '')
    text = text.replace('（', '').replace('）', '')
    text = text.replace('　', '')
    text = text.replace('\n', '').replace('\r', '')
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
        # verify magic header
        if f.read(len(MAGIC)) != MAGIC:
            raise ValueError(f"Invalid magic in {in_path}")
        # number of nodes
        (qty,) = struct.unpack('<I', f.read(4))
        nodes = []
        for _ in range(qty):
            id, type1, ofs, opcode = struct.unpack('<IIII', f.read(16))
            f.read(128)
            (next_id,) = struct.unpack('<I', f.read(4))
            f.read(64)
            # read 33 strings
            strs = [read_str(f) for __ in range(33)]
            nodes.append((id, opcode, next_id, strs))

    # filter opcode == 5 and extract fields
    for item in nodes:
        if item[1] == 5:
            speaker = item[3][1].rstrip('\x00').replace(" ", "")
            if speaker == "":
                continue
            text = text_cleaning(item[3][2].rstrip('\x00'))
            voice = item[3][3].rstrip('\x00').split("\\")[-1].split(".")[0]
            if voice == "":
                continue
            results.append({
                "Speaker": speaker,
                "Voice": voice,
                "Text": text,
            })
    return results


def main():
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    all_entries = []
    for fname in os.listdir(input_dir):
        in_path = os.path.join(input_dir, fname)
        try:
            entries = extract_file(in_path)
            all_entries.extend(entries)
        except Exception as e:
            print(f"Skipping {fname}: {e}")

    # deduplicate by Voice, keeping first occurrence
    unique_entries = []
    seen_voices = set()
    for entry in all_entries:
        voice = entry.get("Voice")
        if voice not in seen_voices:
            seen_voices.add(voice)
            unique_entries.append(entry)

    # write to JSON
    index_path = os.path.join(output_dir, 'index.json')
    with open(index_path, 'w', encoding='utf-8') as jf:
        json.dump(unique_entries, jf, ensure_ascii=False, indent=2)

    print(f"Processed {len(all_entries)} entries, {len(unique_entries)} unique voices saved to {index_path}")


if __name__ == '__main__':
    main()