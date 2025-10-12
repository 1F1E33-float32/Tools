import argparse
import json
import re
from glob import glob

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = re.sub(r"<[^>]*>", "", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "")
    return text


def extract_dialogue(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    instructions = data.get("instructions", [])
    results = []

    speaker = None
    voice = None
    state = "waiting_name"

    for inst in instructions:
        op_name = inst.get("op_name")

        if op_name == "NAME":
            param_comments = inst.get("param_comments", [])
            if param_comments and param_comments[0]:
                speaker = param_comments[0]
                voice = None
                state = "waiting_proc"
            else:
                speaker = None
                voice = None
                state = "waiting_name"

        elif op_name == "PROC":
            params = inst.get("params", [])
            if params and params[0] == 26:
                extra_comment = inst.get("extra_comment")
                if extra_comment and len(extra_comment) > 0:
                    if state == "waiting_proc":
                        voice = extra_comment[0]
                        state = "waiting_text"

        elif op_name == "TEXT":
            if state == "waiting_text":
                param_comments = inst.get("param_comments", [])
                if param_comments and param_comments[0]:
                    text = text_cleaning(param_comments[0])
                    if speaker and voice and text:
                        results.append((speaker, voice, text))
            speaker = None
            voice = None
            state = "waiting_name"

    return results


def main(JA_dir, op_json):
    json_files = glob(f"{JA_dir}/**/*.json", recursive=True)

    all_results = []
    for json_path in tqdm(json_files, ncols=150):
        try:
            results = extract_dialogue(json_path)
            all_results.extend(results)
        except Exception as e:
            print(f"[ERROR] {json_path}: {e}")

    with open(op_json, mode="w", encoding="utf-8") as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in all_results:
            if Voice.lower() not in seen:
                seen.add(Voice.lower())
                json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

    print(f"Total unique dialogues extracted: {len(json_data)}")


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op)
