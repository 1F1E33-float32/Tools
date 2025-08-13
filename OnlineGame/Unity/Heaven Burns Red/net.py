import gzip
import json

def decrypt_bin(data: bytes):
    last = 0
    t = 1156
    out = bytearray(len(data))

    for i, b in enumerate(data):
        # C# 中 (byte)(t ^ last ^ data[i]) 只取低 8 位
        out[i] = (t ^ last ^ b) & 0xFF
        last = b
        # C# int 溢出：按 32 位回绕
        t = (22695477 * t + 1) & 0xFFFFFFFF

    out = bytes(out)
    decompressed = gzip.decompress(bytes(out))
    # 解析 UTF-8 JSON，返回 Python 字典/列表
    return json.loads(decompressed.decode('utf-8'))

with open(r"C:\Users\OOPPEENN\Desktop\push", "rb") as f:
    a = f.read()
    b = decrypt_bin(a)
    print(b)