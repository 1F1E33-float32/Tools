import os
import msgpack
import struct
from tqdm import tqdm
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

PackEncryptKey = 'ARC-PACKPASSWORD'.encode('utf-8')
EncryptKey = 'c6eahbq9sjuawhvdr9kvhpsm5qv393ga'.encode('utf-8')

def read_idx(idx_path):
    pack_infos = []
    with open(idx_path, 'rb') as f:
        while True:
            len_bytes = f.read(4)
            if not len_bytes:
                break
            data_len = struct.unpack('<i', len_bytes)[0]
            encrypted_data = f.read(data_len)
            cipher = AES.new(EncryptKey, AES.MODE_CBC, PackEncryptKey)
            decrypted = cipher.decrypt(encrypted_data)
            try:
                decrypted = unpad(decrypted, AES.block_size)
            except ValueError:
                pass
            info = msgpack.unpackb(decrypted, raw=False)
            pack_infos.append(info)
    return pack_infos

def decrypt_bin(bin_file, index_pos, size):
    with open(bin_file, 'rb') as f:
        f.seek(index_pos)
        encrypted_data = f.read(size)
    cipher = AES.new(EncryptKey, AES.MODE_CBC, PackEncryptKey)
    decrypted = cipher.decrypt(encrypted_data)
    try:
        decrypted = unpad(decrypted, AES.block_size)
    except ValueError:
        pass
    return decrypted

def unpack_files(input_dir, output_dir, base_name):
    idx_path = os.path.join(input_dir, f"{base_name}.idx")
    bin_path = os.path.join(input_dir, f"{base_name}.bin")

    os.makedirs(output_dir, exist_ok=True)

    pack_list = read_idx(idx_path)

    for pack in tqdm(pack_list, ncols=150):
        data = decrypt_bin(bin_path, pack['index'], pack['size'])
        relative_path = os.path.join(output_dir, pack['fileName'][1:])
        os.makedirs(os.path.dirname(relative_path), exist_ok=True)
        with open(relative_path, 'wb') as f:
            f.write(data)

if __name__ == '__main__':
    input_dir = r"E:\BT\Chaos Dominas\Chaosdominus_Data\StreamingAssets"
    output_dir = r"D:\Fuck_galgame"

    unpack_files(input_dir, output_dir, "scripts")
    unpack_files(input_dir, output_dir, "voice")