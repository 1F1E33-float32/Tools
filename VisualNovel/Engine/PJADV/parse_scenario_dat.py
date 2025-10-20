import argparse
import json
from pathlib import Path


def _u32le(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off : off + 4], "little")


def _decode_text_at_foa(textdata: bytes, foa: int, encoding: str = "cp932", errors: str = "replace") -> str:
    if foa <= 0 or foa >= len(textdata):
        return ""
    end = textdata.find(b"\x00", foa)
    if end == -1:
        end = len(textdata)
    return textdata[foa:end].decode(encoding, errors=errors)


def parse_scenario_dat(file_path: str, *, textdata_path: str | None = None, encoding: str = "cp932", errors: str = "replace") -> dict:
    data = Path(file_path).read_bytes()

    if len(data) < 32:
        raise ValueError("scenario.dat too small: missing header")

    sig = data[:12]
    if sig != b"PJADV_SF0001":
        raise ValueError("Invalid signature: expected 'PJADV_SF0001'")

    msg_count = _u32le(data, 12)
    # skip 16 bytes unknown
    cursor = 12 + 4 + 16

    textdata = None
    if textdata_path:
        try:
            textdata = Path(textdata_path).read_bytes()
        except Exception as err:
            raise ValueError(f"Failed to read textdata: {textdata_path}") from err

    commands: list[dict] = []

    size = len(data)
    while cursor < size:
        op = _u32le(data, cursor)
        count = op & 0xFF  # OPCode.ucCount
        # C++ logic: if ucCount > 0x7F or == 0, treat as single dword
        if count == 0 or count > 0x7F:
            dword_len = 1
        else:
            dword_len = count

        byte_len = dword_len * 4
        if cursor + byte_len > size:
            raise ValueError("Unexpected EOF while scanning commands")

        # Extract params following OP
        params = []
        for i in range(1, dword_len):
            params.append(_u32le(data, cursor + i * 4))

        entry: dict = {
            "offset": cursor,
            "op": op,
            "count": dword_len,
            "params": params,
        }

        # Optional resolution for common ops if textdata is provided
        if textdata is not None:
            op_name = None
            resolved: dict = {}
            if op in (0x80000307, 0x80000406):  # text_box_text variants
                op_name = "text_box_text"
                # Known layouts from docs/code comments
                if len(params) >= 3:
                    name_off = params[1]  # foa for character name
                    msg_off = params[2]   # foa for message text
                    resolved["name_offset"] = name_off
                    resolved["msg_offset"] = msg_off
                    resolved["name_text"] = _decode_text_at_foa(textdata, name_off, encoding, errors) if name_off else ""
                    resolved["msg_text"] = _decode_text_at_foa(textdata, msg_off, encoding, errors) if msg_off else ""
            elif op in (0x01010804, 0x01010203):  # select text
                op_name = "select_text"
                if len(params) >= 1:
                    sel_off = params[0]
                    resolved["sel_offset"] = sel_off
                    resolved["sel_text"] = _decode_text_at_foa(textdata, sel_off, encoding, errors) if sel_off else ""
            elif op == 0x01000D02:  # chapter text
                op_name = "chapter_text"
                if len(params) >= 1:
                    chp_off = params[0]
                    resolved["chp_offset"] = chp_off
                    resolved["chp_text"] = _decode_text_at_foa(textdata, chp_off, encoding, errors) if chp_off else ""
            elif op == 0x03000303:  # save/load comment
                op_name = "save_load_comment"
                if len(params) >= 2:
                    com_off = params[1]
                    resolved["com_offset"] = com_off
                    resolved["com_text"] = _decode_text_at_foa(textdata, com_off, encoding, errors) if com_off else ""

            if op_name is not None:
                entry["op_name"] = op_name
                if resolved:
                    entry["resolved"] = resolved

        commands.append(entry)
        cursor += byte_len

    return {
        "info": {
            "signature": "PJADV_SF0001",
            "msg_count": msg_count,
            "command_count": len(commands),
        },
        "commands": commands,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse PJADV scenario.dat (PJADV_SF0001)")
    parser.add_argument("file", help="path to scenario.dat")
    parser.add_argument("--textdata", default=None, help="optional path to textdata.bin for resolving text offsets")
    parser.add_argument("--encoding", default="cp932", help="decode encoding for textdata (default: cp932)")
    parser.add_argument("--errors", default="replace", choices=["strict", "ignore", "replace"], help="decode error policy for textdata")
    parser.add_argument("--json-out", default="", help="optional output JSON path; stdout if omitted")
    args = parser.parse_args()

    result = parse_scenario_dat(args.file, textdata_path=args.textdata, encoding=args.encoding, errors=args.errors)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


