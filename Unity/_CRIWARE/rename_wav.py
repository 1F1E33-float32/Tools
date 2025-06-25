import re
from pathlib import Path

BASE_DIR = Path(r'D:\Fuck_galgame\VOICE')
PATTERN = re.compile(r'\(([^()]*)\)')

wav_files = []
for file in BASE_DIR.glob('*.wav'):
    if file.is_file():
        wav_files.append((file, file.stat().st_size))

wav_files.sort(key=lambda x: x[1], reverse=True)

seen = set()

for file, size in wav_files:
    match = PATTERN.search(file.name)
    if not match:
        print(f"跳过 (无括号匹配)：{file.name}")
        continue

    new_name = f"{match.group(1)}.wav"
    target = BASE_DIR / new_name

    if match.group(1) in seen:
        print(f"删除重复较小文件：{file.name}")
        file.unlink()
    else:
        seen.add(match.group(1))
        if file.name != new_name:
            print(f"重命名：{file.name} -> {new_name}")
            file.rename(target)
        else:
            print(f"文件名已符合目标格式，无需重命名：{file.name}")