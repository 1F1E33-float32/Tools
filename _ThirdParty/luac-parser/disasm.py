import argparse
import sys
from pathlib import Path

from disasm import Disassembler, LuaParseError, parse_lua_bytecode


def decompile_file(path: Path) -> None:
    data = path.read_bytes()
    bytecode = parse_lua_bytecode(data)
    disassembler = Disassembler(bytecode.header.version)

    text_output = disassembler.disassemble_to_txt(bytecode)
    json_output = disassembler.disassemble_to_json(bytecode)

    text_path = path.with_name(path.name + ".dis.txt")
    json_path = path.with_name(path.name + ".dis.json")

    text_path.write_text(text_output, encoding="utf-8")
    json_path.write_text(json_output, encoding="utf-8")


def iter_luac_files(folder: Path):
    for path in folder.rglob("*"):
        if path.is_file() and path.name.lower().endswith(".scb"):
            yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, help="Input folder containing .luac files")
    args = parser.parse_args(argv)

    if not args.folder.exists():
        parser.error(f"folder '{args.folder}' does not exist")
    if not args.folder.is_dir():
        parser.error(f"'{args.folder}' is not a directory")

    processed = 0
    for luac_path in iter_luac_files(args.folder):
        try:
            decompile_file(luac_path)
            processed += 1
        except LuaParseError as exc:
            print(f"[warn] failed to parse {luac_path}: {exc}", file=sys.stderr)
        except OSError as exc:
            print(f"[warn] failed to write outputs for {luac_path}: {exc}", file=sys.stderr)

    if processed == 0:
        print("No .luac files found.", file=sys.stderr)
        return 1

    print(f"Processed {processed} file(s).")
    return 0


if __name__ == "__main__":
    main()