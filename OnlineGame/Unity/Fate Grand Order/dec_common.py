import bz2
import gzip
from cppdael import MODE_CBC, Pkcs7Padding, decrypt_unpad

def get_interleaved_split():
    s1 = "kzdMtpmzqCHAfx00saU1gIhTjYCuOD1JstqtisXsGYqRVcqrHRydj3k6vJCySu3g"
    s2 = "PFBs0eIuunoxKkCcLbqDVerU1rShhS276SAL3A8tFLUfGvtz3F3FFeKELIk3Nvi4"

    b1 = s1.encode('utf-8')
    b2 = s2.encode('utf-8')

    base_data = bytearray()
    base_top  = bytearray()
    # 对 b2，每 4 字节为一组，组索引偶数放 base_data，奇数放 base_top
    for i in range(0, len(b2), 4):
        group = b2[i:i+4]
        if (i // 4) % 2 == 0:
            base_data.extend(group)
        else:
            base_top.extend(group)

    stage_data = bytearray()
    stage_top  = bytearray()
    # 对 b1，按单字节索引，偶数位放 stage_data，奇数位放 stage_top
    for idx, byte in enumerate(b1):
        if idx % 2 == 0:
            stage_data.append(byte)
        else:
            stage_top.append(byte)

    # 转成只读的 bytes 返回
    return bytes(base_data), bytes(base_top), bytes(stage_data), bytes(stage_top)

def decrypt_and_decompress(data, home, info, is_compress):
    decrypted = decrypt_unpad(MODE_CBC, 32, key=home, iv=info[:32], cipher=data, padding=Pkcs7Padding(32))

    if is_compress:
        if decrypted.startswith(b"BZh"):
            return bz2.decompress(decrypted)
        if decrypted.startswith(b"\x1f\x8b\x08"):
            return gzip.decompress(decrypted)

    return decrypted