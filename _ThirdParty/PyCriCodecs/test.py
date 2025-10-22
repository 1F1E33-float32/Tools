import io

import av
import hcadecrypt
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import stft

with open(r"doc\vo_adv_1001011_000.hca", "rb") as f:
    data = f.read()

# 解密
mainkey = 0x000000000030D9E8
subkey = 0x5F3F
decrypted_hca = hcadecrypt.decrypt(data, mainkey, subkey)

# 解码
bio = io.BytesIO(decrypted_hca)
container = av.open(bio, format="hca")

astreams = [s for s in container.streams if s.type == "audio"]
astream = astreams[0]

resampler = av.audio.resampler.AudioResampler(format="fltp", layout="mono")

samples = []
sr = None

for packet in container.demux(astream):
    for frame in packet.decode():
        if sr is None:
            sr = frame.sample_rate
        out_frames = resampler.resample(frame)
        for fr in out_frames:
            arr = fr.to_ndarray()
            if arr.ndim == 2:
                arr = arr[0] if arr.shape[0] == 1 else arr.mean(axis=0)
            samples.append(arr.astype(np.float32))

for fr in resampler.resample(None):  # docs: frame or None to flush
    arr = fr.to_ndarray()
    if arr.ndim == 2:
        arr = arr[0] if arr.shape[0] == 1 else arr.mean(axis=0)
    samples.append(arr.astype(np.float32))

container.close()

y = np.concatenate(samples, axis=0)  # 1D float32

# STFT
n_fft = 2048
hop = 512
win = "hann"
f, t, Zxx = stft(y, fs=sr, window=win, nperseg=n_fft, noverlap=n_fft - hop, nfft=n_fft, boundary="zeros", padded=True)
S_pow = np.abs(Zxx) ** 2  # 功率谱 [freq_bins x time]


# Mel 滤波
def hz_to_mel(f_hz: np.ndarray) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + f_hz / 700.0)


def mel_to_hz(m: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


n_mels = 128
fmin = 0.0
fmax = sr / 2.0

fft_freqs = f

mels = np.linspace(hz_to_mel(fmin), hz_to_mel(fmax), num=n_mels + 2)
hz_points = mel_to_hz(mels)

bin_indices = np.floor((n_fft + 1) * hz_points / sr).astype(int)
bin_indices = np.clip(bin_indices, 0, n_fft // 2)

mel_filters = np.zeros((n_mels, len(fft_freqs)), dtype=np.float32)
for m in range(1, n_mels + 1):
    left = bin_indices[m - 1]
    center = bin_indices[m]
    right = bin_indices[m + 1]

    if center == left:
        center = min(center + 1, len(fft_freqs) - 1)
    if right == center:
        right = min(right + 1, len(fft_freqs) - 1)

    # 上升沿
    mel_filters[m - 1, left:center] = (np.arange(left, center) - left) / float(center - left)
    # 下降沿
    mel_filters[m - 1, center:right] = (right - np.arange(center, right)) / float(right - center)

# 计算每个滤波器的“带宽”，据此缩放
enorm = 2.0 / (hz_points[2:] - hz_points[:-2])  # (n_mels,)
mel_filters *= enorm[:, np.newaxis]

# Mel 功率谱 & 对数
M = mel_filters @ S_pow  # [n_mels x time]
M = np.maximum(M, 1e-10)
M_db = 10.0 * np.log10(M)
M_db -= M_db.max()

# V
plt.figure(figsize=(10, 4))
extent = [t[0], t[-1], fmin, fmax]
plt.imshow(M_db, origin="lower", aspect="auto", extent=[t[0], t[-1], 0, n_mels])
plt.xlabel("Time (s)")
plt.ylabel("Mel bin")
cbar = plt.colorbar()
cbar.set_label("dB")
plt.tight_layout()
plt.show()
