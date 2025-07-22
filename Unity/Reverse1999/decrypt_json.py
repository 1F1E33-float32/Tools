import json
from Crypto.Cipher import AES

def decrypt(dat: bytes) -> bytes:
    cipher = AES.new(
        b"@_#*&Reverse2806                ",
        AES.MODE_CBC,
        b"!_#@2022_Skyfly)"
    )
    decrypted = cipher.decrypt(dat[48:])
    pad_len = decrypted[-1]
    return decrypted[:-pad_len]

def auto_parse(obj):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                try:
                    parsed = json.loads(v)
                except json.JSONDecodeError:
                    continue
                else:
                    obj[k] = auto_parse(parsed)
            else:
                obj[k] = auto_parse(v)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = auto_parse(item)
    return obj

if __name__ == "__main__":
    in_path  = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\datacfg_2.dat"
    out_json = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\datacfg_2.json"

    with open(in_path, "rb") as f:
        raw = f.read()
    decrypted_data = decrypt(raw)

    text = decrypted_data.decode('utf-8')
    data = json.loads(text)

    data = auto_parse(data)

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)