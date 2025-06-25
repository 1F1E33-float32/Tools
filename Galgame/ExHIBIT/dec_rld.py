import struct
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key',        default=r"D:\GAL\#DL\Midori no Umi\key.bin")
    parser.add_argument('-d', '--def-key',    default=r"D:\GAL\#DL\Midori no Umi\key_def.bin")
    parser.add_argument('-i', '--input-dir',  default=r"D:\GAL\#DL\Midori no Umi\rld")
    parser.add_argument('-o', '--output-dir', default=r"D:\GAL\#DL\Midori no Umi\rld_dec")
    return parser.parse_args()

def read_key(path):
    keys = []
    with open(path, 'rb') as f:
        for _ in range(0x100):
            data = f.read(4)
            if len(data) < 4:
                raise EOFError(f"无法从 {path} 读取到足够的 key 数据")
            keys.append(struct.unpack('<L', data)[0])
    return keys

def decrypt_file(src_path, dst_path, key_list, xor_key, max_blocks=0x3ff0):
    with open(src_path, 'rb') as src, open(dst_path, 'wb') as dst:
        header = src.read(0x10)
        dst.write(header)

        src.seek(0, os.SEEK_END)
        filesize = src.tell()
        src.seek(0x10)

        total_blocks = ((filesize - 0x10) >> 2) & 0xffff
        blocks_to_decrypt = min(total_blocks, max_blocks)

        for idx in range(blocks_to_decrypt):
            data = src.read(4)
            if len(data) < 4:
                break
            encrypted_val = struct.unpack('<L', data)[0]
            temp_key = key_list[idx & 0xff] ^ xor_key
            decrypted_val = encrypted_val ^ temp_key
            dst.write(struct.pack('<L', decrypted_val))

        remainder = src.read()
        if remainder:
            dst.write(remainder)

if __name__ == '__main__':
    args = parse_args()

    other_keys = read_key(args.key)
    def_keys = read_key(args.def_key)
    other_xor = 0xCAB01001
    def_xor = 0xAE85A916

    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir
    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith('.rld'):
            continue
        src_path = os.path.join(input_dir, fname)
        base = os.path.splitext(fname)[0]
        dst_name = f"{base}.rld"
        dst_path = os.path.join(output_dir, dst_name)
        print(f"解密: {src_path} -> {dst_path}")

        # 根据文件名选择密钥
        if base.lower() == 'def':
            decrypt_file(src_path, dst_path, def_keys, def_xor)
        else:
            decrypt_file(src_path, dst_path, other_keys, other_xor)