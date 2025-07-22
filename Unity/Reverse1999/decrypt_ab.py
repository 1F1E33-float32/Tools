import io
import os
from multiprocessing import Pool, cpu_count


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
    # 尝试解签名
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


def process_file(args):
    in_path, rel, input_dir, output_dir = args
    out_path = os.path.join(output_dir, rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    stream = decrypt_reverse_1999(in_path)
    with open(out_path, 'wb') as f_out:
        f_out.write(stream.read())


def batch_decrypt_multiprocess(input_dir, output_dir, num_processes=None):
    # 收集所有待处理文件
    file_list = []
    for root, _, files in os.walk(input_dir):
        for name in files:
            in_path = os.path.join(root, name)
            rel = os.path.relpath(in_path, input_dir)
            file_list.append((in_path, rel, input_dir, output_dir))

    # 根据可用CPU和文件数量决定进程数
    if num_processes is None:
        num_processes = min(cpu_count(), len(file_list))

    print(f"Starting decryption with {num_processes} processes...")
    with Pool(processes=num_processes) as pool:
        pool.map(process_file, file_list)

    print('All done.')


if __name__ == '__main__':
    input_dir = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\bundles"
    output_dir = r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\RAW\bundles_dec"
    os.makedirs(output_dir, exist_ok=True)

    batch_decrypt_multiprocess(input_dir, output_dir)