from typing import Union, ByteString


def decrypt_assetbundle(data: Union[bytes, bytearray, memoryview], key_value: int) -> bytearray:
    buf = data if isinstance(data, bytearray) else bytearray(data)
    key32 = key_value & 0xFFFFFFFF                       # 截成无符号 32 bit
    v4 = ((~key32 & 0xFFFFFFFF) << 32) | key32          # 高位是按位取反，低位原样
    for i in range(len(buf)):
        shift = (i & 7) * 8                             # i mod 8 决定取 key 的哪个字节
        buf[i] ^= (v4 >> shift) & 0xFF

    return buf

if __name__ == "__main__":
    with open(r"C:\Users\OOPPEENN\Downloads\VIRTUAL GIRL\Virtual Girl_Data\StreamingAssets\AssetBundles\win\00\1a72a92b33ea2efea8c0c3cc274ed343300bdd915b390241d8cca15d", "rb") as f:
        data = f.read()
    key = 1131378772
    decrypted_data = decrypt_assetbundle(data, key)
    with open(r"decrypted_assetbundle", "wb") as f:
        f.write(decrypted_data)