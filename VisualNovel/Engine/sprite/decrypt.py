import os
import struct
import argparse
import numpy as np
from tqdm import tqdm

global mod, mod1
mod = 2 ** 32
mod1 = 2 ** 31

def gk(k):
    num = (k * 7391 + 42828) % mod
    num2 = (num << 17 ^ num) % mod
    out = []
    for i in range(256):
        num = (num - k + num2) % mod
        num2 = (num + 56) % mod
        num = (num * (num2 & 239)) % mod
        out.append(num & 255)
        num = num >> 1
    return out

def dd(data, k):
    arr = np.frombuffer(data, dtype=np.uint8).copy()
    key = np.array(gk(k), dtype=np.uint8)
    n = arr.size
    indices_253 = np.arange(n) % 253
    indices_89  = np.arange(n) % 89
    arr = np.bitwise_xor(arr, key[indices_253])
    arr = arr + 3 + key[indices_89]
    arr = np.bitwise_xor(arr, 153)
    return arr.tobytes()

def getInfo(f):
    f.seek(0)
    header = f.read(1024)
    num = 0
    num = (sum(struct.unpack(251 * "i", header[16:-4])) + mod1) % mod - mod1
    raw = dd(f.read(16 * num), struct.unpack("I", header[212:216])[0])
    start = struct.unpack("I", raw[12:16])[0]
    array = dd(f.read(start - 1024 - 16 * num), struct.unpack("I", header[92:96])[0])
    out = []
    for i in range(num):
        l, offset, k, p = struct.unpack("IIII", raw[16 * i:16 * (i + 1)])
        name = array[offset:array.find(0, offset)].decode("ascii")
        out.append((name, p, l, k))
    return out

def extract(f, files, out):
    for name, p, l, k in tqdm(files):
        name = os.path.join(out, name)
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, "wb") as o:
            f.seek(p)
            data = dd(f.read(l), k)
            o.write(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a .dat file and optionally extract contents.")
    parser.add_argument("--input_path", default=r"E:\Games\Galgame\sprite\Ao no Kanata no Four Rhythm\Aokana_Data\system.dat")
    parser.add_argument("--output_path", default=r"E:\Games\Galgame\sprite\Ao no Kanata no Four Rhythm\Aokana_Data\system_ext")

    args = parser.parse_args()

    f = open(args.input_path, "rb")
    files = getInfo(f)

    if args.output_path:
        extract(f, files, args.output_path)