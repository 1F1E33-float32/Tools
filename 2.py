import re
from pathlib import Path
from typing import List

def extract_db_bytes(lines: List[str]) -> List[int]:
    """
    Given an iterable of lines like 'db 56h ; V', return a list of integers [0x56, ...].
    """
    hex_pattern = re.compile(r'\b([0-9A-Fa-f]+)h\b')
    out = []
    for ln in lines:
        m = hex_pattern.search(ln)
        if m:
            out.append(int(m.group(1), 16))
    return out

# Example usage:
asm_file = Path("dump.asm")
with asm_file.open(encoding="utf-8") as f:
    byte_list = extract_db_bytes(f)

print(byte_list)