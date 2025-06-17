import hashlib
import string

_alphabet = string.digits + string.ascii_lowercase

txt = "桜ルート八日目-07"
txt_enc = txt.encode("utf-8")

md5 = hashlib.md5(txt_enc)
digest = md5.digest()

bits = int.from_bytes(digest, byteorder='big')
print(bits)
result = ""
for i in range(3, 3 + 128, 5):
    digit = (bits << i >> 128) & 0x1F
    result += _alphabet[digit]

print(result)
