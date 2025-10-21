import base64
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA1
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad

PASSWORD = b"qC8dx9I93EyaMp"
SALT = bytes([49, 110, 49, 102, 49, 108, 51, 39, 53, 95, 53, 52, 108, 55, 95, 118, 52, 108, 117, 51])
IV = bytes([77, 52, 225, 184, 143, 77, 49, 225, 184, 187, 107, 77, 52, 225, 185, 137])

ITERATIONS = 1000
KEY_LENGTH = 32

INI_PATH = Path(r"E:\VN\_tmp\2019_07\Taimanin Yukikaze 2\data.ini")
ENCODING = "utf-8"


def derive_key(password: bytes, salt: bytes) -> bytes:
    # PBKDF2 with HMAC-SHA1 (与 cryptography 版本保持一致)
    return PBKDF2(password, salt, dkLen=KEY_LENGTH, count=ITERATIONS, hmac_hash_module=SHA1)


def decrypt_base64(b64_data: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    padded_plain = cipher.decrypt(base64.b64decode(b64_data))
    # AES 块大小 16 字节 => block_size=16
    return unpad(padded_plain, block_size=16)


if __name__ == "__main__":
    b64_cipher = INI_PATH.read_bytes().strip()
    key = derive_key(PASSWORD, SALT)
    decrypted_bytes = decrypt_base64(b64_cipher, key, IV)
    plaintext = decrypted_bytes.decode(ENCODING, errors="replace")
    print(plaintext)
