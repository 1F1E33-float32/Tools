import re
import sys
from pathlib import Path
from collections import Counter

# Base directory containing .wav files
BASE_DIR = Path(r'D:\Fuck_galgame\voice')
PATTERN = re.compile(r"\(([^()]*)\)")

# First pass: collect all base names and associated files
entries = []  # list of tuples (file_path, base_name)
for file in BASE_DIR.glob('*.wav'):
    if not file.is_file():
        continue
    match = PATTERN.search(file.name)
    if not match:
        print(f"跳过 (无括号匹配)：{file.name}")
        continue
    base_name = match.group(1)
    entries.append((file, base_name))

# Detect duplicates in base names
base_names = [base for _, base in entries]
counter = Counter(base_names)
duplicates = [name for name, count in counter.items() if count > 1]
if duplicates:
    print("检测到重复的括号内容，程序退出。重复项如下：")
    for dup in duplicates:
        print(f"- {dup}")

# No duplicates: proceed to sort by file size (desc) and rename/delete
# Sort entries by file size descending
entries.sort(key=lambda x: x[0].stat().st_size, reverse=True)

seen = set()
for file, base in entries:
    new_name = f"{base}.wav"
    target = BASE_DIR / new_name

    # If this base name was already processed, delete the smaller file
    if base in seen:
        print(f"删除重复较小文件：{file.name}")
        file.unlink()
    else:
        seen.add(base)
        if file.name != new_name:
            print(f"重命名：{file.name} -> {new_name}")
            file.rename(target)
        else:
            print(f"文件名已符合目标格式，无需重命名：{file.name}")