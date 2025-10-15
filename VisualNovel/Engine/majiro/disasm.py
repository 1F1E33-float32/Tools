import argparse
from pathlib import Path

from majiro_disasm.disassembler import Disassembler


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default=r"D:\Fuck_VN\script")
    args = parser.parse_args()

    folder_path = Path(args.folder)
    mjo_files = list(folder_path.glob("*.mjo"))

    for mjo_file in mjo_files:
        txt_file = mjo_file.with_suffix(".txt")
        json_file = mjo_file.with_suffix(".json")
        
        print(f"Disassembling {mjo_file.name}...")
        
        script = Disassembler.disassemble_from_file(str(mjo_file))
        
        with open(txt_file, "w", encoding="utf-8") as f:
            Disassembler.print_script(script, f)
        
        with open(json_file, "w", encoding="utf-8") as f:
            Disassembler.render_to_json(script, f)