from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import gzip, io

def decrypt(data: bytes) -> bytes:
    # 与 C# 保持一致：ASCII 字节
    key = b"xO?Nrk(x.+ICI5K!"           # 16 字节
    iv  = b"L.!9yaNJy.a{lFwF"           # 16 字节 (AES 块大小)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(data) + decryptor.finalize()

    # .NET 对称算法默认 PKCS7 填充
    unpadder = padding.PKCS7(128).unpadder()  # 128 表示块大小（bit）
    decrypted = unpadder.update(padded) + unpadder.finalize()

    # 解 GZip
    with gzip.GzipFile(fileobj=io.BytesIO(decrypted)) as gz:
        return gz.read()
    
with open(r"C:\Users\OOPPEENN\Desktop\catalog_19d94261a8f308766e45b3cf9ab49333259b8319.json", "rb") as f:
    data = f.read()

plaintext = decrypt(data)
with open(r"C:\Users\OOPPEENN\Desktop\catalog_19d94261a8f308766e45b3cf9ab49333259b8319.json.dec", "wb") as f:
    f.write(plaintext)