import base64

import xxhash


class Mt19937:
    N = 624
    M = 397
    MATRIX_A = 0x9908B0DF
    UPPER_MASK = 0x80000000
    LOWER_MASK = 0x7FFFFFFF

    def __init__(self, seed: int):
        self.state = [0] * self.N
        self.idx = self.N
        self.reseed(seed & 0xFFFFFFFF)

    def reseed(self, seed: int):
        self.idx = self.N
        self.state[0] = seed & 0xFFFFFFFF
        for i in range(1, self.N):
            self.state[i] = (1812433253 * (self.state[i - 1] ^ (self.state[i - 1] >> 30)) + i) & 0xFFFFFFFF

    def _fill_next_state(self):
        for i in range(0, self.N - self.M):
            x = (self.state[i] & self.UPPER_MASK) | (self.state[i + 1] & self.LOWER_MASK)
            self.state[i] = (self.state[i + self.M] ^ (x >> 1) ^ (self.MATRIX_A if (x & 1) else 0)) & 0xFFFFFFFF
        for i in range(self.N - self.M, self.N - 1):
            x = (self.state[i] & self.UPPER_MASK) | (self.state[i + 1] & self.LOWER_MASK)
            self.state[i] = (self.state[i + self.M - self.N] ^ (x >> 1) ^ (self.MATRIX_A if (x & 1) else 0)) & 0xFFFFFFFF
        x = (self.state[self.N - 1] & self.UPPER_MASK) | (self.state[0] & self.LOWER_MASK)
        self.state[self.N - 1] = (self.state[self.M - 1] ^ (x >> 1) ^ (self.MATRIX_A if (x & 1) else 0)) & 0xFFFFFFFF
        self.idx = 0

    def next_u32(self) -> int:
        if self.idx >= self.N:
            self._fill_next_state()
        x = self.state[self.idx]
        self.idx += 1
        x ^= x >> 11
        x ^= (x << 7) & 0x9D2C5680
        x ^= (x << 15) & 0xEFC60000
        x ^= x >> 18
        return x & 0xFFFFFFFF


def next_bytes(rng: Mt19937, length: int) -> bytes:
    buf = bytearray(length)
    num_chunks = (length + 3) // 4
    for i in range(num_chunks):
        num = (rng.next_u32() >> 1) & 0x7FFFFFFF
        offset = i * 4
        end = min(offset + 4, length)
        for j in range(offset, end):
            shift = (j - offset) * 8
            buf[j] = (num >> shift) & 0xFF
    return bytes(buf)


def derive_password(filename: str) -> bytes:
    name = filename
    h = xxhash.xxh32(name.encode("utf-8"), seed=0).intdigest() & 0xFFFFFFFF
    rng = Mt19937(h)
    raw = next_bytes(rng, 15)
    return base64.b64encode(raw)
