import os, base64, hashlib
from typing import Optional

from Crypto.Cipher import AES          # pip install pycryptodome
from Crypto.Util.Padding import pad, unpad
import lz4.block                       # pip install lz4
import msgpack, requests


# ------------------------------------------------------------
# 共用小工具
# ------------------------------------------------------------

def _md5(data: bytes) -> bytes:
    return hashlib.md5(data).digest()


def _hex16(s: str) -> bytes:
    """
    把十六进制 / UUID 字符串变成 16 字节，不足补 0x00，超出截断
    """
    s = s.replace("-", "")
    raw = bytes.fromhex(s)
    return (raw + b"\x00" * 16)[:16]


def _derive_key_iv(sid_hex: str, udid_hex: str, header_b64: str):
    """
    复现 C# 中的密钥 / IV 生成逻辑
    """
    header = base64.b64decode(header_b64)            # 32 B
    tail20 = header[-20:]                            # 固定取后 20 B

    sid  = _hex16(sid_hex)                           # 16 B
    udid = _hex16(udid_hex)                          # 16 B

    key = _md5(sid + tail20)                         # 16 B
    iv  = _md5(udid + tail20)                        # 16 B
    return key, iv, header


# ------------------------------------------------------------
# 加密（发送请求）
# ------------------------------------------------------------

def encrypt_request(payload: bytes,
                    sid_hex: str,
                    udid_hex: str,
                    header_b64: str,
                    authkey_b64: Optional[str] = None) -> str:
    """
    返回 ready-to-POST 的 Base64 字符串
    """
    key, iv, header = _derive_key_iv(sid_hex, udid_hex, header_b64)

    # ❶ 组装可变头部
    rnd = bytearray(os.urandom(32))
    rnd[0] = 0          # platform id = 0

    head_parts = [
        _hex16(sid_hex),
        _hex16(udid_hex),
        rnd
    ]
    if authkey_b64:
        head_parts.append(base64.b64decode(authkey_b64))
    head = b"".join(head_parts)

    # ❷ AES-CBC 加密业务数据
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc    = cipher.encrypt(pad(payload, AES.block_size))

    # ❸ 拼接 & 混淆
    full  = bytearray(len(head).to_bytes(4, "little") + head + enc)

    for i in range(32):
        full[i + 4] ^= rnd[i]
        full[i + 4] ^= header[i]

    return base64.b64encode(full).decode()


# ------------------------------------------------------------
# 解密（处理服务器响应）
# ------------------------------------------------------------

def decrypt_response(b64_text: str,
                     sid_hex: str,
                     udid_hex: str,
                     header_b64: str) -> bytes:
    """
    传入服务器返回的 Base64 字符串，得到明文字节
    """
    key, iv, header = _derive_key_iv(sid_hex, udid_hex, header_b64)
    buf = bytearray(base64.b64decode(b64_text))

    # 1) 还原 rnd、解除 XOR
    rnd = bytearray(32)
    for i in range(32):
        rnd[i]  = buf[i + 4] ^ header[i]
        buf[i + 4] ^= rnd[i]

    # 2) 取出加密负载
    head_len = int.from_bytes(buf[:4], "little")
    enc_part = bytes(buf[4 + head_len:])

    # 3) AES-CBC 解密
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plain  = unpad(cipher.decrypt(enc_part), AES.block_size)

    # 4) 判断是否 LZ4 压缩
    if buf[4] != 0:               # 第 5 个字节非 0 代表压缩
        plain = lz4.block.decompress(plain)

    return plain


header_b64 = "YOUR_STATIC_HEADER_BASE64"
sid  = "72A6F0...DEADBEEF"        # 16-32 hex 字符
udid = "123e4567-e89b-12d3-a456-426614174000"

request_obj = {"viewer_id": 123456789012, "param": "value"}
payload     = msgpack.packb(request_obj, use_bin_type=True)

body_b64 = encrypt_request(payload, sid, udid, header_b64)
resp     = requests.post("https://l13-prod-all-gs-uma.komoejoy.com/...")
plain    = decrypt_response(resp.text, sid, udid, header_b64)
answer   = msgpack.unpackb(plain, raw=False)

print(answer)