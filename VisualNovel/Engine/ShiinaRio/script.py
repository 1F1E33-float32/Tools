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
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "").replace("　", "")

    # 正则匹配 <左/右> 结构并替换
    pat = re.compile(r"<([^/<>]+?)/([^<>]+?)>")

    def repl(m):
        left, right = m.group(1), m.group(2)
        # 仅当左边全由日文中点「・」组成时，用右边替换
        if left and all(ch == "・" for ch in left):
            return right
        # 否则用左边
        return left

    return re.sub(pat, repl, text)


def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.TXT", recursive=True)

    results = []

    for filename in tqdm(filelist, ncols=150):
        try:
            with open(filename, "r", encoding="cp932") as file:
                lines = file.readlines()
        except Exception:
            with open(filename, "r", encoding="euc-jp") as file:
                lines = file.readlines()

        i = 0
        while i < len(lines):
            if lines[i].startswith(";"):
                i += 1
                continue

            voice_match = re.compile(r"\$VOICE,v\\(\w+\.ogv)").search(lines[i])
            if voice_match:
                Voice = voice_match.group(1).replace(".ogv", "").replace(".ogg", "")
                Speaker_id = Voice.split("_")[0]
                i += 1

                while i < len(lines):
                    if lines[i].startswith(";"):
                        i += 1
                        continue

                    speaker_match = re.compile(r"【([^】]+)】").search(lines[i])
                    if speaker_match:
                        Speaker = speaker_match.group(1)
                        Speaker = Speaker.split("/")[0]
                        i += 1

                        text_lines = []
                        while i < len(lines):
                            if lines[i].strip() == "":
                                i += 1
                                break
                            if lines[i].startswith(";"):
                                i += 1
                                continue
                            text_lines.append(lines[i].strip())
                            i += 1

                        Text = "".join(text_lines)
                        Text = text_cleaning(Text)
                        results.append((Speaker, Speaker_id, Voice, Text))
                        break  # 跳出 speaker 匹配的循环
                    else:
                        i += 1
            else:
                i += 1

    replace_dict = {}
    for Speaker, Speaker_id, Voice, Text in tqdm(results, ncols=150):
        if Speaker != "？？？" and Speaker_id not in replace_dict:
            replace_dict[Speaker_id] = Speaker

    fixed_results = []
    for Speaker, Speaker_id, Voice, Text in tqdm(results, ncols=150):
        if Speaker == "？？？" and Speaker_id in replace_dict:
            fixed_results.append((replace_dict[Speaker_id], Speaker_id, Voice, Text))
        else:
            fixed_results.append((Speaker, Speaker_id, Voice, Text))

    with open(op_json, mode="w", encoding="utf-8") as file:
        seen = set()
        json_data = []
        for Speaker, Speaker_id, Voice, Text in fixed_results:
            if Voice not in seen:
                seen.add(Voice)
                json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op)
