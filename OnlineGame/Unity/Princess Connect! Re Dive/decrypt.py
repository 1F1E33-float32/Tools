from base64 import b64decode
from typing import Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def _decrypt(data: bytes) -> Tuple[bytes, bytes]:
    data = b64decode(data)
    
    key = data[-32:]
    iv = b"ha4nBYA2APUD6Uv1"
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    decrypted = decryptor.update(data[:-32]) + decryptor.finalize()
    
    return decrypted

if __name__ == "__main__":
    a = r"wN4AA3JJTFHk4A2tqxt0egko85Ze1DcHzxsz7r2pRuWFxqTzAHokq0R5SwWM4JAlXTxv0cEnf+tYEb5hK6+WnB6D/XNHK5YppcflB46RTzA+/ZoKWL0KEIu+CzfVcG+vj7hvW+x0qD8vGbjeXo2g3FZVecTPbWo8FJiA7R4So8IJ04b/ajQK1fYHWaFv9artsq5eCDTkNvo7lv857px7USyRIdhfhvpVw3kkzsonEhpIRX94KWRdq0sHIjzlbzlvDXFFAwUSggo37ALqerPbDT/gn3vVHAPWTlvQpO2Emh72TzDHXLg24XsZIg+KguHgKQVodJ6UAx0DMKjOklExcC0obMd1P3oik5f0fuYc2TmJawKt9afA5xcw0yLf0W18MQJT/WbrTuEHEgN/S4I4m8XPPMoTFa3toaNJhGKJMkG5BeTOnBEA7Ln/H9OMaqqlyB4nw7DSeAdnUBh/5geOav84tFt7BwK5yid9NWKHi24XAKTJfHv1n4q75n6725GV11SDLeVtI6YmLntz/X1SUVH6IkLB4tMvkQJeduv0uYqxW9/98KTvJfmEIvSulUGbNFd8eoc98QDvhQRTVAuuluYTLVGBC4YwnexRIYUJ"

    b = _decrypt(a)
    print(b)