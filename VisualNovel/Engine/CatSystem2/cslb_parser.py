import argparse
import json
import zlib

from cs2_utils import Reader


def _decode_payload(b):
    r = Reader(b)
    if r.read(4) != b"CSLB":
        raise ValueError
    original_len = r.read_int_le()
    comp_len = r.read_int_le()
    if original_len <= 0:
        raise ValueError
    if comp_len == 0:
        payload = r.read(original_len)
        return payload
    mode = r.read_int_le()
    comp = r.read(comp_len)
    try:
        payload = zlib.decompress(comp)
    except Exception:
        payload = zlib.decompress(comp, -zlib.MAX_WBITS)
    return payload


def _parse_tree(r, files):
    count = r.read_varint()
    out = {}
    for _ in range(count):
        name = r.read_string()
        idx = r.read_varint()
        if idx < 0 or idx >= len(files):
            raise ValueError
        child = _parse_tree(r, files)
        out[name] = {"file": files[idx], "children": child}
    return out


def parse_cslb_bytes(data):
    payload = _decode_payload(data)
    r = Reader(payload)
    n = r.read_varint()
    files = []
    for _ in range(n):
        files.append(r.read_string())
    return _parse_tree(r, files)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=r"E:\VN\ja\ensemble\Kyokkou no Marriage\CatSystem\scene\@labels.cslb")
    p.add_argument("--output", default=r"E:\VN\ja\ensemble\Kyokkou no Marriage\CatSystem\scene\@labels.json")
    args = p.parse_args()
    with open(args.input, "rb") as f:
        data = f.read()
    obj = parse_cslb_bytes(data)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)
