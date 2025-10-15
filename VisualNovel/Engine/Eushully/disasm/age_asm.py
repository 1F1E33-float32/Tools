import argparse
from pathlib import Path

from disassembler import disassemble
from renderers import JsonRenderer, TextRenderer


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    return parser


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def write_outputs(ir, base_path: Path, text_renderer: TextRenderer, json_renderer: JsonRenderer):
    txt_path = base_path.with_suffix(".txt")
    json_path = base_path.with_suffix(".json")

    txt_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    text_result = text_renderer.render(ir)
    json_result = json_renderer.render(ir)

    with open(txt_path, "w", encoding="utf-8") as f_txt:
        f_txt.write(text_result)

    with open(json_path, "w", encoding="utf-8") as f_json:
        f_json.write(json_result)


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    input_path: Path = args.input
    output_path: Path | None = args.output

    text_renderer = TextRenderer()
    json_renderer = JsonRenderer()

    if input_path.is_dir():
        out_dir = output_path if output_path is not None else Path("decompiled")
        ensure_dir(out_dir)

        for file in input_path.glob("*.[bB][iI][nN]"):
            if file.stat().st_size == 0:
                continue

            base = out_dir / file.stem
            print(f"Disassembling {file}")
            with open(file, "rb") as f_in:
                ir = disassemble(f_in)
            write_outputs(ir, base, text_renderer, json_renderer)

    else:
        if output_path is None:
            base = input_path.with_suffix("")
        else:
            if output_path.exists() and output_path.is_dir():
                base = output_path / input_path.stem
            else:
                base = output_path.with_suffix("")

        print(f"Disassembling {input_path} into {base.with_suffix('.txt')} and {base.with_suffix('.json')}")
        with open(input_path, "rb") as f_in:
            ir = disassemble(f_in)
        write_outputs(ir, base, text_renderer, json_renderer)
