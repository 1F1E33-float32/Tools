import io, os

def get_ab_encrypt_key(md5_name):
    key = sum(ord(c) for c in md5_name) & 0xFF
    return (key + 2 * ((key & 1) + 1)) & 0xFF

def decrypt_reverse_1999(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    sig_bytes = bytearray(data[:8])
    sig = sig_bytes[:7].decode('utf-8', errors='ignore')
    # 如果已经是 UnityFS，直接返回原始流
    if sig == 'UnityFS':
        print(f'[SKIP] UnityFS: {file_path}')
        return io.BytesIO(data)

    stem = os.path.splitext(os.path.basename(file_path))[0]
    key = get_ab_encrypt_key(stem)
    # 试图解签名
    for i in range(len(sig_bytes)):
        sig_bytes[i] ^= key
    sig = sig_bytes[:7].decode('utf-8', errors='ignore')
    # 如果解出 UnityFS，继续解剩余数据
    if sig == 'UnityFS':
        rem = bytearray(data[8:])
        for i in range(len(rem)):
            rem[i] ^= key

        out = io.BytesIO()
        out.write(sig_bytes)
        out.write(rem)
        out.seek(0)
        print(f'[DECRYPT] {file_path}')
        return out

    # 既不是明文也不是 reverse-1999
    print(f"[WARN] Not encrypted: {file_path}")
    return io.BytesIO(data)

def batch_decrypt(input_dir, output_dir):
    for root, _, files in os.walk(input_dir):
        for name in files:
            in_path = os.path.join(root, name)
            rel = os.path.relpath(in_path, input_dir)
            out_path = os.path.join(output_dir, rel)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            stream = decrypt_reverse_1999(in_path)
            with open(out_path, 'wb') as f_out:
                f_out.write(stream.read())

if __name__ == '__main__':
    input_dir  = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\language"
    output_dir = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\configs\language_dec"
    os.makedirs(output_dir, exist_ok=True)
    batch_decrypt(input_dir, output_dir)
    print('All done.')