# Reference: https://github.com/robbie01/stcm2-asm

import argparse
from pathlib import Path
from typing import Dict, Optional

from disasm import run as disasm_run
from ruamel.yaml import YAML


def load_mnemonics(config_path: Optional[Path]) -> Dict[int, str]:
    if config_path is None or not config_path.exists():
        return {0: "return"}

    try:
        yaml = YAML(typ="safe", pure=True)
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.load(f)

        if config is None or "mnemonics" not in config:
            return {0: "return"}

        mnemonics_config = config["mnemonics"]
        if not isinstance(mnemonics_config, dict):
            print("Warning: 'mnemonics' in config is not a dict, using defaults")
            return {0: "return"}

        # Expect {opcode:int -> name:str}
        mnemonics: Dict[int, str] = {}
        for opcode, name in mnemonics_config.items():
            if not isinstance(opcode, int):
                # Try to coerce numeric strings to int
                if isinstance(opcode, str) and opcode.isdigit():
                    opcode = int(opcode)
                else:
                    print(f"Warning: opcode key {opcode!r} is not int, skipping")
                    continue
            if not isinstance(name, str):
                print(f"Warning: mnemonic name {name!r} for opcode {opcode} is not a string, skipping")
                continue
            mnemonics[opcode] = name

        return mnemonics
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {0: "return"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", type=Path, default=Path(r"D:\Fuck_VN\text"))
    parser.add_argument("--config", type=Path, default=Path(r"VisualNovel\Engine\IDEA FACTORY\feature\悠久のティアブレイド -Lost Chronicle-\config.yaml"))
    args = parser.parse_args()

    mnemonics = load_mnemonics(args.config)
    print(f"Loaded {len(mnemonics)} mnemonics")

    disasm_run(args.in_dir, mnemonics)
