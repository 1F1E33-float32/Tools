# Reference: https://github.com/robbie01/stcm2-asm

import argparse
from pathlib import Path

from disasm import run as disasm_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir", type=Path)
    args = parser.parse_args()

    disasm_run(args.in_dir)
