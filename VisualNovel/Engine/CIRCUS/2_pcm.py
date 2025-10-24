import os
import struct
from glob import glob

import tools_boost
from tqdm import tqdm


def write_wav(pcm_data: bytes, sample_rate: int, channels: int, bits_per_sample: int, output_path: str) -> None:
    byte_rate = sample_rate * channels * (bits_per_sample // 8)
    block_align = channels * (bits_per_sample // 8)
    data_size = len(pcm_data)

    riff_header = struct.pack("<4sI4s", b"RIFF", 36 + data_size, b"WAVE")
    fmt_chunk = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
    data_header = struct.pack("<4sI", b"data", data_size)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(riff_header)
        f.write(fmt_chunk)
        f.write(data_header)
        f.write(pcm_data)


def process_one(input_file: str, in_root: str, out_root: str) -> None:
    rel = os.path.relpath(input_file, in_root)
    rel_dir = os.path.dirname(rel)
    base_no_ext = os.path.splitext(os.path.basename(rel))[0]

    with open(input_file, "rb") as f:
        data = f.read()

    pcm_or_stream, meta = tools_boost.xpcm_extractor.xpcm_to_pcm(data)

    codec = meta.get("codec", -1)
    sample_rate = meta.get("sample_rate", 0)
    channels = meta.get("channels", 0)
    bits_per_sample = meta.get("bits_per_sample", 16)

    if codec == 0x05:
        ext = ".ogg"
    elif codec in (0x00, 0x02, 0x01, 0x03):
        ext = ".wav"
    else:
        ext = f".codec_{codec:02X}"

    out_dir_full = os.path.join(out_root, rel_dir)
    os.makedirs(out_dir_full, exist_ok=True)
    out_path = os.path.join(out_dir_full, base_no_ext + ext)

    if codec == 0x05:
        with open(out_path, "wb") as f:
            f.write(pcm_or_stream)
    else:
        write_wav(pcm_or_stream, sample_rate, channels, bits_per_sample, out_path)


def main(in_dir: str, out_dir: str) -> None:
    pattern = os.path.join(in_dir, "**", "*.pcm")
    files = glob(pattern, recursive=True)
    for path in tqdm(files, ncols=150):
        process_one(path, in_dir, out_dir)


if __name__ == "__main__":
    in_dir = r"D:\Fuck_VN\pcm"
    out_dir = r"D:\Fuck_VN\voice"

    main(in_dir, out_dir)
