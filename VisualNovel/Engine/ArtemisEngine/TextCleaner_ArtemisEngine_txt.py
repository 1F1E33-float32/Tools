import argparse
import json
import re
from glob import glob

from tqdm import tqdm


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\scenario")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_galgame\index.json")
    parser.add_argument("-ft", type=float, default=0)
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("▼", "").replace("　", "").replace("●", "")
    text = re.sub(r'\[ruby text="[^"]*"\](.*?)\[/ruby\]', r"\1", text)
    text = re.sub(r'\[[^\]]*?rb\s*=\s*"[^/"]*/([^"]*)"\]', r"\1", text)
    return text


def main(JA_dir, op_json, force_type):
    filelist = glob(f"{JA_dir}/**/*.txt", recursive=True)
    results = []
    for filename in tqdm(filelist):
        try:
            with open(filename, "r", encoding="cp932") as file:
                content = file.read()
        except Exception:
            with open(filename, "r", encoding="utf-8") as file:
                content = file.read()
        cleaned_content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        lines = cleaned_content.splitlines()
        lines = [line for line in lines if not re.match(r"^\s*(//|#)", line)]

        for i, line in enumerate(lines):
            match force_type:
                case 0:
                    match = re.findall(r"\[name\s+(\S+)\s+(\S+)\]", line)
                    if match:
                        match = match[0]
                        Speaker = match[0]
                        Voice = match[1]

                        Text = ""
                        j = i + 1

                        while j < len(lines) and lines[j].strip() != "":
                            Text += lines[j]
                            j += 1

                        Text = text_cleaning(Text)
                        results.append((Speaker, Voice, Text))
                case 1:
                    match = re.match(r"\[([^=]+?)\s+((?:\w+\s*=\s*\"[^\"]*\"\s*)+)\]", line)
                    if match:
                        Speaker = match.group(1).strip()
                        # 提取所有键值对
                        key_values = re.findall(r'(\w+)\s*=\s*"([^"]*)"', match.group(2))
                        attributes = dict(key_values)
                        Voice = attributes.get("file")
                        if Voice is None:
                            continue  # 如果没有找到file属性则跳过
                        # 检查Speaker是否仅包含字母数字（原逻辑）
                        if re.fullmatch(r"[A-Za-z0-9\-\_]+", Speaker):
                            continue
                        Text = lines[i + 1]
                        Text = text_cleaning(Text)
                        results.append((Speaker, Voice, Text))

    with open(op_json, mode="w", encoding="utf-8") as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            if Voice.lower() not in seen:
                seen.add(Voice.lower())
                json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, args.ft)
