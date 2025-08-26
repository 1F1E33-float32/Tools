import struct
import os

def read_key(path):
    keys = []
    with open(path, 'rb') as f:
        for _ in range(0x100):
            data = f.read(4)
            if len(data) < 4:
                raise EOFError(f"无法从 {path} 读取到足够的 key 数据")
            keys.append(struct.unpack('<L', data)[0])
    return keys

def read_xor(path):
    text = open(path, 'r', encoding='utf-8').read().strip()
    if text.lower().startswith('0x'):
        return int(text, 16)
    return int(text)

def decrypt_file(src_path, dst_path, key_list, xor_key, max_blocks=0x3FF0):
    with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
        header = src.read(0x10)
        dst.write(header)

        src.seek(0, os.SEEK_END)
        filesize = src.tell()
        src.seek(0x10)

        total_blocks = ((filesize - 0x10) >> 2) & 0xFFFF
        blocks_to_decrypt = min(total_blocks, max_blocks)

        for idx in range(blocks_to_decrypt):
            data = src.read(4)
            if len(data) < 4:
                break
            encrypted_val = struct.unpack('<L', data)[0]
            temp_key = key_list[idx & 0xFF] ^ xor_key
            decrypted_val = encrypted_val ^ temp_key
            dst.write(struct.pack('<L', decrypted_val))

        remainder = src.read()
        if remainder:
            dst.write(remainder)

if __name__ == '__main__':
    script_dir    = r"D:\GAL\2025_01\Natsu e no Hakobune III"
    output_dir    = r"D:\Fuck_galgame\rld_dec"
    key_path      = os.path.join(script_dir, 'key.bin')
    def_key_path  = os.path.join(script_dir, 'key_def.bin')
    xor_path      = os.path.join(script_dir, 'key.txt')
    def_xor_path  = os.path.join(script_dir, 'key_def.txt')
    input_dir     = os.path.join(script_dir, 'rld')

    other_keys = read_key(key_path)
    def_keys   = read_key(def_key_path)

    other_xor = read_xor(xor_path)
    def_xor   = read_xor(def_xor_path)

    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith('.rld'):
            continue
        src_path = os.path.join(input_dir, fname)
        base     = os.path.splitext(fname)[0]
        dst_name = f"{base}.rld"
        dst_path = os.path.join(output_dir, dst_name)
        print(f"解密: {src_path} -> {dst_path}")

        if base.lower() == 'def':
            decrypt_file(src_path, dst_path, def_keys, def_xor)
        else:
            decrypt_file(src_path, dst_path, other_keys, other_xor)