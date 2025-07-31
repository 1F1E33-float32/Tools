import os
import base64
import argparse
from glob import glob
from dec_common import decrypt_and_decompress, get_interleaved_split

def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default=r"E:\Game_Dataset\com.aniplex.fategrandorder\EXP\Story_ENC")
    parser.add_argument("--output", type=str, default=r"E:\Game_Dataset\com.aniplex.fategrandorder\EXP\Story_DEC")
    return parser.parse_args()

base_data, base_top, stage_data, stage_top = get_interleaved_split()

def mouse_game3(encoded_str):
    data = base64.b64decode(encoded_str)

    result = decrypt_and_decompress(data, stage_data, stage_top, True)
    if result is None:
        return None

    inverted = bytes((~b & 0xFF) for b in result)

    return inverted.decode('utf-8').rstrip('\x00')

if __name__ == "__main__":
    args = args_parser()
    filelist = glob(args.root + r"\**\*.txt", recursive=True)

    for file in filelist:
        with open(file, "r", encoding="utf-8") as f:
            data = f.read()
            try:
                result = mouse_game3(data)
            except Exception as e:
                print(f"Error processing {file}: {e}")
                continue
            out_path = os.path.join(args.output, os.path.relpath(file, args.root))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as out_f:
                out_f.write(result)