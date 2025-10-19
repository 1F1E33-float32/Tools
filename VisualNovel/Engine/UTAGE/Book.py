import argparse
import json
import re


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=r"D:\Fuck_VN\book.json")
    parser.add_argument("--op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = re.sub(r"<[^<>]+>", "", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace(" ", "").replace("　", "").replace("\n", "").replace("\r", "")
    return text


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

    result = []

    grids = data["importGridList"]

    for grid in grids:
        rows = grid["rows"]

        header = rows[0]["strings"]

        for r in rows[1:]:
            values = r["strings"]
            row_map = row_to_map(header, values)

            Voice = row_map["Voice"]
            if Voice is None:
                continue
            Voice = Voice.replace(".ogg", ".wav")

            Speaker = row_map["Arg1"]
            if Speaker is None:
                Speaker = "？？？"

            Speaker = Speaker.replace(" ", "").replace("　", "").replace("?", "？")

            Text = row_map["Text"]
            if Text is None:
                continue
            Text = text_cleaning(Text)

            result.append((Speaker, Voice, Text))

    with open(op_json, mode="w", encoding="utf-8") as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in result:
            if Voice not in seen:
                seen.add(Voice)
                json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.input, args.op)
