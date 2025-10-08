import argparse
from pathlib import Path

from disasm import disasm_run
from ruamel.yaml import YAML


def load_mnemonics(config_path):
    mnemonics = {0: "return"}

    if config_path is None or not config_path.exists():
        return mnemonics

    try:
        yaml = YAML(typ="safe", pure=True)
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.load(f)

        if config is None or "mnemonics" not in config:
            return mnemonics

        mnemonics_config = config["mnemonics"]
        if not isinstance(mnemonics_config, dict):
            print("Warning: 'mnemonics' in config is not a dict, using defaults")
            return mnemonics

        for opcode, name in mnemonics_config.items():
            if not isinstance(opcode, int):
                if isinstance(opcode, str) and opcode.isdigit():
                    opcode = int(opcode)
                else:
                    print(f"Warning: opcode key {opcode!r} is not int, skipping")
                    continue
            if not isinstance(name, str):
                print(f"Warning: mnemonic name {name!r} for opcode {opcode} is not a string, skipping")
                continue
            mnemonics[opcode] = name

        if 0 not in mnemonics:
            mnemonics[0] = "return"
            print("Info: Added default mnemonic {0: 'return'}")

        return mnemonics
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {0: "return"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--in_dir", default=Path(r"D:\Fuck_VN\script"))
    parser.add_argument("--config", default=Path())

    parser.add_argument("--addr", action="store_true", default=False)
    parser.add_argument("--junk", action="store_true", default=False)

    parser.add_argument("--emit-txt", action="store_true", default=True)
    parser.add_argument("--emit-json", action="store_true", default=True)

    args = parser.parse_args()

    mnemonics = load_mnemonics(args.config)
    print(f"Loaded {len(mnemonics)} mnemonics from config")

    disasm_run(in_dir=args.in_dir, mnemonics=mnemonics, print_junk=args.junk, show_address=args.addr, emit_txt=args.emit_txt, emit_json=args.emit_json)
