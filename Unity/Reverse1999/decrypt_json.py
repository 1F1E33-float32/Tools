from Crypto.Cipher import AES
import json

cipher = AES.new(b"@_#*&Reverse2806                ", AES.MODE_CBC, b"!_#@2022_Skyfly)")

def decrypt(dat):
    decrypted = cipher.decrypt(dat[48:])
    pad_len = decrypted[-1]
    return decrypted[:-pad_len] if 1 <= pad_len <= 9 else decrypted

def extract_inner_json(obj: dict):
    for key, val in obj.items():
        if isinstance(val, str) and val.lstrip().startswith(('[', '{')):
            return val
    raise KeyError("No inner JSON string field found")

if __name__ == "__main__":
    in_path  = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\language\json_language_server_en.json.dat"
    out_path = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\language\json_language_server_en.json"

    with open(in_path, "rb") as f:
        raw = f.read()
    decrypted_data = decrypt(raw)

    text = decrypted_data.decode('utf-8')
    outer = json.loads(text)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(outer, f, ensure_ascii=False, indent=4)

    print(f"Extracted inner JSON with {len(outer)} top‐level elements")