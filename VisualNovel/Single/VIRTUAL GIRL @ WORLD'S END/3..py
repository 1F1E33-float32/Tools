import ctypes
import argparse
from pathlib import Path

def decrypt_assetbundle(buf: bytearray, key_value: int) -> None:
    if not isinstance(buf, bytearray):
        buf = bytearray(buf)

    key_hi_xor = ((key_value << 32) & 0xFFFFFFFFFFFFFFFF) ^ 0xFFFFFFFF00000000
    key_sign64 = ctypes.c_int64(key_value).value & 0xFFFFFFFFFFFFFFFF
    key64      = (key_hi_xor | key_sign64) & 0xFFFFFFFFFFFFFFFF

    kbytes = key64.to_bytes(8, "little")

    mv = memoryview(buf)
    for i in range(len(mv)):
        mv[i] ^= kbytes[i & 7]

    return buf

def main(root_path: Path, mapping_file: Path, output_root: Path):
    with mapping_file.open('r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or ',' not in line:
                continue
            rel_path, key_str = line.split(',', 1)
            try:
                key = int(key_str)
            except ValueError:
                print(f"[Line {lineno}] Invalid key '{key_str}', skipping.")
                continue

            input_path = root_path / rel_path
            if not input_path.is_file():
                print(f"[Line {lineno}] File not found: {input_path}, skipping.")
                continue

            output_path = output_root / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Read, decrypt, and write
            encrypted_data = input_path.read_bytes()
            decrypted_data = decrypt_assetbundle(encrypted_data, key)
            output_path.write_bytes(decrypted_data)
            print(f"[Line {lineno}] Decrypted: {input_path} -> {output_path}")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_path", default=Path(r"C:\Users\OOPPEENN\Downloads\GAL\VIRTUAL GIRL\Virtual Girl_Data\StreamingAssets\AssetBundles\win"))
    parser.add_argument("--mapping_file", default=Path(r"D:\Project\Tools\Galgame\_Single\VIRTUAL GIRL @ WORLD'S END\assetbundles_hashed.txt"))
    parser.add_argument("--output_root", default=Path('decrypted_assetbundles'))
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args.root_path, args.mapping_file, args.output_root)