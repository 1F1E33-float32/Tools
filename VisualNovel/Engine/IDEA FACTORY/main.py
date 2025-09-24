import argparse
from pathlib import Path

from disasm import run as disasm_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir", type=Path, help="Input directory containing .DAT files")
    args = parser.parse_args()

    disasm_run(args.in_dir)
