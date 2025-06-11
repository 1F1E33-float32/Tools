import hmac
import base64
import msgpack
import hashlib
import requests

from datetime import datetime, timezone

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def get_windows_filetime():
    windows_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - windows_epoch
    filetime = int(delta.total_seconds() * 10**7)
    return filetime

class Builtin:
    elements = [
        "4dn9Sycy!ev)8f%_,Yay~pAj)~k4q!hNz,FHuWHFQe%+P*eW24Ac)yTAGeF$pJ)!7BU!9#ke%|3Ai%*jMa(Vi~B2j*L(uyvE/9cE$E_,WwV4irL$5RXgaC4ufu/4FB5p",
        "j%.i.LL|rL,+d6JA",
        "EZTv,6~NZQv(X9DU"
    ]
    def cnv(src):
        return ''.join(src[2 * i + 1] for i in range(len(src) // 2))

    def get_key(index):
        return Builtin.cnv(Builtin.elements[index])

class AppCryptoConfig:
    def hash_key():
        return Builtin.get_key(0)

    def hash_salt():
        return Builtin.get_key(1)

    def crypto_key():
        raw = Builtin.get_key(2)
        return Hash.hash_string(raw, 16)

    def get_hash_algorithm(secret_key_bytes):
        return hmac.new(secret_key_bytes, digestmod=hashlib.sha256)


class Hash:
    def get_salt():
        salt = AppCryptoConfig.hash_salt()
        return salt[0] + salt[1:]

    def get_hash_key():
        key = AppCryptoConfig.hash_key()
        key = key[0] + key[1:]
        return key.encode('utf-8')

    def hash_bytes(text, max_length):
        v8 = Hash.get_salt() + text
        hmac_obj = AppCryptoConfig.get_hash_algorithm(Hash.get_hash_key())
        hmac_obj.update(v8.encode('utf-8'))
        digest = hmac_obj.digest()

        if max_length == 0 or len(digest) < max_length:
            return digest

        offset = (len(digest) - max_length) // 2
        return digest[offset:offset + max_length]

    def hash_string(text, max_length):
        raw_bytes = Hash.hash_bytes(text, max_length)
        base64_str = base64.b64encode(raw_bytes).decode('utf-8')
        if len(base64_str) > max_length:
            start = (len(base64_str) - max_length) // 2
            return base64_str[start:start + max_length]
        return base64_str

class BasicCrypto:
    def decrypt(crypto_key, data):
        iv = data[:len(crypto_key)]
        ciphertext = data[len(crypto_key):]
        cipher = AES.new(crypto_key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ciphertext), len(crypto_key), style='pkcs7')

    def encrypt(crypto_key, raw, iv):
        cipher = AES.new(crypto_key, AES.MODE_CBC, iv)
        padded = pad(raw, len(crypto_key), style='pkcs7')
        encrypted = cipher.encrypt(padded)
        return iv + encrypted

class ApiCrypto:
    MsgPackAppCryptoKey = "UVFBdDtWKhpESJj3"

    def decrypt(encrypted_bytes):
        key = ApiCrypto.MsgPackAppCryptoKey
        hashkey_str = Hash.hash_string(key, 16)
        hashkey = hashkey_str.encode('utf-8')
        return BasicCrypto.decrypt(hashkey, encrypted_bytes)

    def encrypt(raw_bytes, iv_bytes):
        key = ApiCrypto.MsgPackAppCryptoKey
        hashkey_str = Hash.hash_string(key, 16)
        hashkey = hashkey_str.encode('utf-8')
        return BasicCrypto.encrypt(hashkey, raw_bytes, iv_bytes)

    def to_timestamp(dt: datetime):
        # Convert to UTC and return integer seconds since Unix epoch
        utc_dt = dt.astimezone(timezone.utc)
        return int(utc_dt.timestamp())

    def sign(encrypted_bytes, private_key_bytes):
        # Step 1: SHA1 hash over encrypted_bytes
        sha1_1 = hashlib.sha1()
        sha1_1.update(encrypted_bytes)
        hashed1 = sha1_1.digest()  # bytes

        # Step 2: Base64 encode that hash
        data = base64.b64encode(hashed1)  # bytes

        # Step 3: SHA1 hash over the UTF-8 bytes of the Base64 string
        sha1_2 = hashlib.sha1()
        sha1_2.update(data)
        hashed2 = sha1_2.digest()  # bytes

        # Step 4: Load private key (PKCS#8 DER format) and sign the second hash using SHA1, PKCS#1 v1.5 padding
        private_key = serialization.load_der_private_key(private_key_bytes, password=None)
        signature = private_key.sign(
            hashed2,
            asym_padding.PKCS1v15(),
            utils.Prehashed(hashes.SHA1())
        )

        # Step 5: Return signature as Base64 string
        return base64.b64encode(signature).decode('utf-8')
    
class Game_API:
    def __init__(self):
        self.API_URL   = "https://api-gl.mmme.pokelabo.jp"
        self.ASSET_URL = "https://static-masterdata-mmme.akamaized.net"

        self.UNITY_VER = "2022.3.21f1"
        self.APP_VER   = "1.4.0"

        self.SEED = "UVFBdDtWKhpESJj3"
        self.IV = "8846515530616782552cab5e1d7c850f"

        self.session = requests.Session()

    def _post(self, url, data=None, headers=None, **kw):
        return self.session.post(url, data=data, headers=headers, **kw)
    
    def _get(self, url, headers=None, **kw):
        return self.session.get(url, headers=headers, **kw)

    def call_game(self, endpoint, data):
        data_enc = ApiCrypto.encrypt(msgpack.packb(data), bytes.fromhex(self.IV))

        headers = {
            "Host": "api-gl.mmme.pokelabo.jp",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "User-Agent": "UnityRequest   (Xiaomi 24031PN0DC Android OS 12 / API-32 (V417IR/1113))",
            "X-GAME-SERVER-URL": self.API_URL,
            "x-region": "US",
            "x-language": "en-Latn",
            "x-timezone-offset": "28800",
            "x-app-version": self.APP_VER,
            "X-Unity-Version": self.UNITY_VER
            }
        
        resp = self._post(self.API_URL + endpoint, data=data_enc, headers=headers)
        resp.raise_for_status()

        raw = resp.content
        decrypted = ApiCrypto.decrypt(raw)

        result = msgpack.unpackb(decrypted, raw=False)
        return result
    
if __name__ == "__main__":
    data = {'payload': {'storeType': 2, 'appVersion': f"{Game_API().APP_VER}", 'sm': '', 'lastHomeAccessTime': ''},
            'uuid': None, 'userId': 0, 'sessionId': None, 'actionToken': None, 'ctag': None, 'actionTime': get_windows_filetime()}
    Game_API().call_game("/api/app_version/get_review_version_data", data)

    '''
    {'url': '/api/app_version/get_review_version_data', 'status': 200,
    'payload': {'isReviewVersion': False, 'appealTitleInfo': {'titleResourceName': '10070101', 'homeResourceName': '10070101', 'startTime': '2025-05-30T12:00:00+09:00', 'endTime': '2025-06-12T11:59:59+09:00'}}}
    '''
    data = {'payload': {'osType': 2, 'storeType': 2, 'appVersion': f"{Game_API().APP_VER}", 'sm': 'd005c1c66149eee78c53194ec78ebd5d4o0033FFAB03CC2C81CB6113EE012BCB49AADDB57E03n', 'lastHomeAccessTime': ''},
            'uuid': '9348356922677095ae41fa6224f7fbb3fefcd6f0003fff6', 'userId': 0, 'sessionId': None, 'actionToken': None, 'ctag': None, 'actionTime': get_windows_filetime()}
    Game_API().call_game("/api/title/get_title_top_data", data)

    '''
    {'url': '/api/title/get_title_top_data', 'status': 200,
    'payload': {'viewData': {'isMaintenance': False, 'isDbMaintenance': False, 'maintenanceMessage': '', 'dbMaintenanceForAnnounceText': 'News is temporarily unavailable due to database maintenance.'}, 'privacyUrl': 'https://madoka-exedra.com/en/privacy/us.html'}}
    '''