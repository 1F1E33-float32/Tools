import base64
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PASSWORD = b"qC8dx9I93EyaMp"
SALT = bytes([49, 110, 49, 102, 49, 108, 51, 39, 53, 95, 53, 52, 108, 55, 95, 118, 52, 108, 117, 51])
IV = bytes([77, 52, 225, 184, 143, 77, 49, 225, 184, 187, 107, 77, 52, 225, 185, 137])

ITERATIONS = 1000
KEY_LENGTH = 32

INI_PATH = Path(r"D:\GAL\2019_07\Taimanin Yukikaze 2\data.ini")
ENCODING = "utf-8"


def derive_key(password, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA1(), length=KEY_LENGTH, salt=salt, iterations=ITERATIONS, backend=default_backend())
    return kdf.derive(password)


def decrypt_base64(b64_data, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(base64.b64decode(b64_data)) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_plain) + unpadder.finalize()


if __name__ == "__main__":
    b64_cipher = INI_PATH.read_bytes().strip()
    key = derive_key(PASSWORD, SALT)
    decrypted_bytes = decrypt_base64(b64_cipher, key, IV)
    plaintext = decrypted_bytes.decode(ENCODING, errors="replace")

    print(plaintext)
