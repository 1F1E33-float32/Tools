from a3 import Blowfish

# V_CODE
resource = b'\x6F\x06\xFF\xF6\xD6\x00\xD2\x4D\xC1\x70\xE1\xD3\x6F\xF5\xB2\x7D'

# KEY_CODE
key_resource = b'\x8B\x9F\x82\x83\x99\x9A\x84\x83\x8A'
key = bytearray(key_resource)
for i in range(len(key)):
    key[i] ^= 205
key = bytes(key)

# 初始化 Blowfish 密码器（ECB 模式）
cipher = Blowfish(key)

# 确保数据长度为 8 的倍数，并进行解密
decrypt_length = (len(resource) // 8) * 8
decrypted = cipher.decrypt(resource[:decrypt_length])

# 查找第一个 0 字节的位置
try:
    num2 = decrypted.index(0)
except ValueError:
    num2 = len(decrypted)

# 使用 cp932 编码解码字符串
decoded_text = decrypted[:num2].decode('cp932', errors='ignore')

print(decoded_text)