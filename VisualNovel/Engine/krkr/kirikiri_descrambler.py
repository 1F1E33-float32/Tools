import argparse
import io
import os
import struct
import zlib
from pathlib import Path
from typing import List, Optional, Union

MAGIC = b"\xfe\xfe"
BOM_UTF16LE = b"\xff\xfe"
TEXT_EXTENSIONS = {".ks", ".tjs", ".txt", ".csv", ".ini"}


def _descramble_mode0(data: bytearray) -> bytes:
    for i in range(0, len(data), 2):
        # If this looks like ASCII (00 high byte) and control char, leave as-is
        if data[i + 1] == 0 and data[i] < 0x20:
            continue
        data[i + 1] ^= data[i] & 0xFE
        data[i] ^= 0x01
    return bytes(data)


def _descramble_mode1(data: bytearray) -> bytes:
    for i in range(0, len(data), 2):
        c = data[i] | (data[i + 1] << 8)
        c = ((c & 0xAAAA) >> 1) | ((c & 0x5555) << 1)
        data[i] = c & 0xFF
        data[i + 1] = (c >> 8) & 0xFF
    return bytes(data)


def _decompress(stream: io.BufferedReader) -> bytes:
    # Read <q (compressed length), <q (uncompressed length)
    comp_len_bytes = stream.read(8)
    if len(comp_len_bytes) != 8:
        raise ValueError("Unexpected EOF reading compressed length")
    uncomp_len_bytes = stream.read(8)
    if len(uncomp_len_bytes) != 8:
        raise ValueError("Unexpected EOF reading uncompressed length")
    comp_len = struct.unpack("<q", comp_len_bytes)[0]
    uncomp_len = struct.unpack("<q", uncomp_len_bytes)[0]

    if comp_len < 0:
        raise ValueError("Negative compressed length in header")
    if uncomp_len < 0:
        raise ValueError("Negative uncompressed length in header")

    # Read exactly comp_len bytes which should be a zlib stream
    zdata = stream.read(comp_len)
    if len(zdata) != comp_len:
        raise ValueError("Unexpected EOF reading zlib payload")

    # Decompress as zlib-wrapped stream
    out = zlib.decompress(zdata)
    if len(out) != uncomp_len:
        # Keep going but warn via exception to let caller decide
        raise ValueError(f"Decompressed size mismatch: expected {uncomp_len}, got {len(out)}")
    return out


def descramble_bytes(data: bytes) -> Optional[str]:
    # Verify magic
    if len(data) < 5:
        return None
    if data[0:2] != MAGIC:
        return None

    mode = data[2]
    if data[3:5] != BOM_UTF16LE:
        return None

    payload = memoryview(data)[5:]
    if mode == 0:
        if len(payload) % 2 != 0:
            raise ValueError("Mode 0 payload not even-length for UTF-16LE")
        decoded = _descramble_mode0(bytearray(payload))
    elif mode == 1:
        if len(payload) % 2 != 0:
            raise ValueError("Mode 1 payload not even-length for UTF-16LE")
        decoded = _descramble_mode1(bytearray(payload))
    elif mode == 2:
        with io.BytesIO(payload.tobytes()) as bio:
            decoded = _decompress(bio)
    else:
        raise NotImplementedError(f"Unsupported scrambling mode {mode}")

    # Payload is UTF-16LE-encoded text
    return decoded.decode("utf-16-le")


def descramble_path(path: Union[os.PathLike, str]) -> Optional[str]:
    with open(path, "rb") as f:
        data = f.read()
    return descramble_bytes(data)


def _descramble_folder(folder: Path) -> None:
    for root, _, files in os.walk(folder):
        for name in files:
            ext = Path(name).suffix.lower()
            if ext not in TEXT_EXTENSIONS:
                continue
            fpath = Path(root) / name
            try:
                result = descramble_path(fpath)
                if result is None:
                    continue
                fpath.write_text(result, encoding="utf-8")
                print(f"Descrambled {fpath}")
            except Exception as ex:
                print(f"Failed to descramble {fpath}: {ex}")


def _descramble_file(path: Path) -> None:
    try:
        result = descramble_path(path)
        if result is None:
            print("File is not scrambled.")
            return
        path.write_text(result, encoding="utf-8")
        print("File descrambled.")
    except Exception as ex:
        print(f"Failed to descramble file: {ex}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Kirikiri descrambler (Python)")
    # Allow top-level path to mimic previous CLI when no subcommand is used
    parser.add_argument("path", nargs="?", help="Path to file or folder")

    args = parser.parse_args(argv)

    target_str = args.path

    if not target_str:
        parser.print_usage()
        print("Usage: kirikiri_descrambler.py <file/folder>")
        return 1

    target = Path(target_str)
    if target.is_dir():
        _descramble_folder(target)
    elif target.is_file():
        _descramble_file(target)
    else:
        print("Specified file or folder does not exist.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())