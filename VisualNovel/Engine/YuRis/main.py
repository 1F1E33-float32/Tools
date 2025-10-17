import argparse
import struct
import sys
from pathlib import Path

from decompiler.yscd import YSCD
from decompiler.yuris_script import YuRisScript

DEFAULT_KEY = struct.pack("<I", 0x2939099B)


def args_parse(argv=None):
    parser = argparse.ArgumentParser(
        description="YuRis script analyze tool",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  yuris_tool.py -r D:\\game\\ysbin -k 0x4A415E60\n"
            "  yuris_tool.py -r . -k 4A 41 5E 60\n"
            '  yuris_tool.py -r . -k "4A,41,5E,60"\n'
            "  yuris_tool.py -r . --format json\n"
            "  yuris_tool.py -r . --format txt+json"
        ),
    )
    parser.add_argument(
        "-r",
        "--root",
        dest="root",
        metavar="DIR",
        default=r"D:\Fuck_VN\ysbin",
        help="Root directory containing ysc.ybn/ysl.ybn/yst_list.ybn, etc.",
    )
    parser.add_argument(
        "-c",
        "--yscd",
        "--yscom",
        dest="yscom",
        metavar="FILE",
        help="Path to YSCD file (optional).",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        metavar="FORMAT",
        default="txt+json",
        help="Output format: txt | json | txt+json (default: txt).",
    )
    parser.add_argument(
        "-k",
        "--key",
        dest="key_tokens",
        nargs="+",
        metavar="VALUE",
        help="YBN key as 32-bit hex (e.g. 0x4A415E60) or 4 bytes.",
    )
    parser.add_argument(
        "positional_root",
        nargs="?",
        metavar="DIR",
        help="Positional fallback for root directory.",
    )
    parser.add_argument(
        "positional_yscom",
        nargs="?",
        metavar="FILE",
        help="Positional fallback for YSCD file.",
    )

    parsed = parser.parse_args(argv)

    root = parsed.root or parsed.positional_root
    yscom = parsed.yscom or parsed.positional_yscom

    if not root:
        parser.error("missing --root (or positional root).")

    if not Path(root).is_dir():
        parser.error(f"Root directory not found: {root}")

    if yscom and not Path(yscom).is_file():
        parser.error(f"YSCD file not found: {yscom}")

    ybn_key = DEFAULT_KEY
    if parsed.key_tokens:
        try:
            ybn_key = parse_key(parsed.key_tokens)
        except ValueError as exc:
            parser.error(f"--key: {exc}")

    # Parse output format
    fmt = parsed.format.strip().lower()
    if fmt not in ("txt", "json", "txt+json"):
        parser.error(f"Unknown --format: {parsed.format}. Supported: txt, json, txt+json")

    output_format = fmt

    return argparse.Namespace(root=root, yscom=yscom, ybn_key=ybn_key, output_format=output_format)


def parse_key(tokens):
    if len(tokens) == 1:
        t = tokens[0].strip()

        # Check for comma/separator list in single token
        parts = [p.strip() for p in t.replace(",", " ").replace("-", " ").replace(":", " ").split() if p.strip()]

        if len(parts) == 1:
            # Single 32-bit hex value
            if t.startswith("0x") or t.startswith("0X"):
                t = t[2:]

            if len(t) > 8 or len(t) == 0 or not all(c in "0123456789abcdefABCDEF" for c in t):
                raise ValueError("expect 32-bit hex (e.g., 4A415E60)")

            value = int(t, 16)
            return struct.pack("<I", value)  # Little-endian

        elif len(parts) == 4:
            # 4 bytes in single token
            return bytes([parse_byte(p) for p in parts])
        else:
            raise ValueError("expect 4 bytes or 32-bit hex")

    elif len(tokens) == 4:
        # 4 separate byte tokens
        return bytes([parse_byte(t) for t in tokens])
    else:
        raise ValueError("--key expects 1 value (hex32) or 4 byte values")


def parse_byte(s: str) -> int:
    s = s.strip()

    if s.startswith("0x") or s.startswith("0X"):
        s = s[2:]

    # Try decimal first
    if s.isdigit():
        value = int(s, 10)
        if value > 255:
            raise ValueError(f"invalid byte: {s}")
        return value

    # Try hex
    try:
        value = int(s, 16)
        if value > 255:
            raise ValueError(f"invalid hex byte: {s}")
        return value
    except ValueError:
        raise ValueError(f"invalid hex byte: {s}")

def main(argv=None):
    args = args_parse(argv)

    if args.yscom:
        YSCD.load(args.yscom)

    try:
        yuris = YuRisScript()
        yuris.init(args.root, args.ybn_key)

        if args.output_format == "json":
            yuris.decompile_project_json()
        elif args.output_format == "txt":
            yuris.decompile_project()
        elif args.output_format == "txt+json":
            # Output both formats
            yuris.decompile_project()
            yuris.decompile_project_json()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
