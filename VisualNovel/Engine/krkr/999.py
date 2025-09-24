import re


def parse_macros(file_path):
    with open(file_path, "r", encoding="utf-16-le") as f:
        content = f.read()

    pattern = re.compile(
        r"\[macro\s+name=(?P<macro>[^\]]+)\]\s*"
        r'\[eval\s+exp="f\.history_need_name=\'【(?P<name>[^】]+)】\'"\]',
        re.DOTALL,
    )

    matches = list(pattern.finditer(content))
    mapping = {}

    for idx, m in enumerate(matches):
        macro = m.group("macro").strip()
        name = m.group("name").strip()
        print(f"{idx}: {macro} → {name}")
        mapping[macro] = name

    return mapping


if __name__ == "__main__":
    file_path = r"D:\Fuck_galgame\system\func.ks"
    result_dict = parse_macros(file_path)
    print("\n最终映射字典：")
    print(result_dict)
