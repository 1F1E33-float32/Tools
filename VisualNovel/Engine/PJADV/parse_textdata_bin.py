import argparse
import json
from pathlib import Path


def parse_textdata_bin(file_path: str, encoding: str = "cp932", errors: str = "replace") -> dict:
    file_bytes = Path(file_path).read_bytes()

    if len(file_bytes) < 16:
        raise ValueError("textdata.bin too small: missing header")

    signature = file_bytes[:12]
    if signature != b"PJADV_TF0001":
        raise ValueError("Invalid signature: expected 'PJADV_TF0001'")

    text_count = int.from_bytes(file_bytes[12:16], "little")

    texts = []
    offsets = []

    cursor = 16
    file_size = len(file_bytes)

    for _ in range(text_count):
        if cursor >= file_size:
            raise ValueError("Unexpected EOF while scanning text entries")

        # Find single NUL terminator, then ensure double-NUL separator
        try:
            nul_pos = file_bytes.index(0, cursor)
        except ValueError as err:
            raise ValueError("Missing NUL terminator for text entry") from err

        entry_bytes = file_bytes[cursor:nul_pos]
        offsets.append(cursor)
        try:
            entry_str = entry_bytes.decode(encoding, errors=errors)
        except Exception as err:
            raise ValueError("Failed to decode text entry") from err
        texts.append(entry_str)

        # Expect double-NUL (0x00 0x00)
        next_pos = nul_pos + 1
        if next_pos >= file_size:
            # Tolerate single NUL at end, but warn by raising informative error
            raise ValueError("Unexpected EOF after single NUL; expected double-NUL separator")
        if file_bytes[next_pos] != 0:
            # Not a double-NUL; still advance one to avoid infinite loop
            cursor = next_pos
        else:
            cursor = next_pos + 1

    return {
        "info": {
            "signature": "PJADV_TF0001",
            "text_count": text_count,
        },
        "offsets": offsets,  # offsets of each string (FOA) in this file
        "texts": texts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse PJADV textdata.bin (PJADV_TF0001)")
    parser.add_argument("file", help="path to textdata.bin")
    parser.add_argument("--encoding", default="cp932", help="decode encoding (default: cp932)")
    parser.add_argument("--errors", default="replace", choices=["strict", "ignore", "replace"], help="decode error policy")
    parser.add_argument("--json-out", default="", help="optional output JSON path; stdout if omitted")
    args = parser.parse_args()

    result = parse_textdata_bin(args.file, args.encoding, args.errors)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


