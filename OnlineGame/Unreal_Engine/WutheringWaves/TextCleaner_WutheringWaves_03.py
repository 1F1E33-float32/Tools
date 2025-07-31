import argparse
import json
import shutil
from pathlib import Path

LANGS = ["en", "ko"]
TYPES = ["favorwords", "flowstate"]

def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def main(inp: Path, outp: Path, dry_run: bool = False):
    for lang in LANGS:
        records = []
        for t in TYPES:
            src_json = inp / f"{lang}_{t}.json"
            if not src_json.exists():
                print(f"[WARN] {src_json} not found, skip.")
                continue
            print(f"[INFO] Reading {src_json}")
            data = load_json(src_json)
            if not isinstance(data, list):
                print(f"[WARN] {src_json} is not a list, skip.")
                continue

            for item in data:
                voice_path_str = item.get("Voice")
                speaker = item.get("Speaker", "Unknown")
                if not voice_path_str:
                    print(f"[WARN] Missing Voice in item: {item}")
                    continue

                voice_src = Path(voice_path_str)
                if not voice_src.is_absolute():
                    voice_src = (inp.parent / voice_src).resolve()

                filename_only = Path(voice_path_str).name  # <--- 只保留文件名+后缀

                dst_dir = outp / lang / speaker
                dst_file = dst_dir / filename_only
                ensure_dir(dst_dir)

                if voice_src.exists():
                    shutil.copy2(voice_src, dst_file)
                else:
                    print(f"[MISS] Voice file not found: {voice_src}")

                new_item = {k: v for k, v in item.items() if k != "RoleId"}
                new_item["Voice"] = filename_only  # <--- 核心修改
                records.append(new_item)

        if records:
            index_path = outp / lang / "index.json"
            ensure_dir(index_path.parent)
            with index_path.open("w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=4)
            print(f"[OK] {index_path} written. ({len(records)} entries)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default=r"D:\Dataset_Game\WutheringWaves\EXP")
    parser.add_argument("--output", default=r"D:\Dataset_VN_NoScene\#OK L\Wuwa")
    args = parser.parse_args()

    main(Path(args.input), Path(args.output))