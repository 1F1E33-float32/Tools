import base64
import xxhash

N, M = 624, 397
MATRIX_A = 0x9908B0DF
UPPER_MASK = 0x80000000
LOWER_MASK = 0x7FFFFFFF

def mt19937_u32_stream(seed):
    mt = [0] * N
    mt[0] = seed & 0xFFFFFFFF
    for i in range(1, N):
        mt[i] = (1812433253 * (mt[i - 1] ^ (mt[i - 1] >> 30)) + i) & 0xFFFFFFFF

    idx = N
    while True:
        if idx >= N:
            for i in range(N):
                y = (mt[i] & UPPER_MASK) | (mt[(i + 1) % N] & LOWER_MASK)
                mt[i] = mt[(i + M) % N] ^ (y >> 1) ^ (MATRIX_A if (y & 1) else 0)
            idx = 0

        y = mt[idx]
        idx += 1
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= (y >> 18)
        yield y & 0xFFFFFFFF

def next_bytes(seed, length=15):
    rng = mt19937_u32_stream(seed)
    out = bytearray(length)

    for i in range((length + 3) // 4): 
        num = next(rng) >> 1
        offset = i * 4
        for j in range(4):
            idx = offset + j
            if idx < length:
                out[idx] = (num >> (j * 8)) & 0xFF
    return bytes(out)

def compute_zip_password(filename):
    seed = xxhash.xxh32(filename.encode("utf-8")).intdigest()
    rnd_bytes = next_bytes(seed, 15)
    return base64.b64encode(rnd_bytes).decode("ascii")

if __name__ == "__main__":
    filename = r"Excel.zip"
    password = compute_zip_password(filename)
    print(f"Computed password for '{filename}': {password}")