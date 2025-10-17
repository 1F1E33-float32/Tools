import argparse
import json
import re


CHAR_RE = re.compile(r"<\s*Character\s*=\s*([^>]+)\s*>", re.IGNORECASE)


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=r"D:\Fuck_VN\Scenario.book.json")
    parser.add_argument("--op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace(" ", "")
    return text


def extract_speaker_id(arg2: str) -> str:
    m = CHAR_RE.search(arg2)
    return m.group(1).strip()


def row_to_map(header, values):
    m = {}
    for i, key in enumerate(header):
        if key == "":
            key = f"PAD_{i}"
        if i >= len(values):
            m[key] = None
        elif values[i] == "":
            m[key] = None
        else:
            m[key] = values[i]

    return m


def main(input_path, op_json):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grids = data["importGridList"]

    for grid in grids:
        rows = grid["rows"]

        header = rows[0]["strings"]

        for r in rows[1:]:
            values = r["strings"]
            row_map = row_to_map(header, values)

            Voice = row_map['Voice']
            if  Voice is None:
                continue

            Speaker = row_map['Arg1']
            ID = row_map['Arg2']
            if Speaker is None and ID is None:
                Speaker = "？？？"

            if Speaker is None:
                pass

            Speaker = text_cleaning(Speaker)

            #speaker_id = extract_speaker_id(arg2)

            #blocks.append({"voice": cleaned_voice, "text": cleaned_text, "arg1": arg1, "arg2": arg2, "speaker_id": speaker_id})


if __name__ == "__main__":
    args = parse_args()
    main(args.input, args.op)
