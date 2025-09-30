import re
from typing import List, Tuple


def count_tokens(line: str) -> Tuple[int, int]:
    """Return (# of '%[' occurrences, # of ']' occurrences) in a line.
    We don't strictly ignore strings; envinit.tjs rarely contains these tokens in strings.
    """
    opens = len(re.findall(r"%\[", line))
    closes = line.count("]")
    return opens, closes


def parse_envinit_characters(text: str) -> List[Tuple[str, str, str]]:
    lines = text.splitlines()
    results: List[Tuple[str, str, str]] = []

    # Locate the characters block
    start_idx = None
    for i, line in enumerate(lines):
        if '"characters"' in line and "=> %[" in line:
            start_idx = i
            break
    if start_idx is None:
        raise SystemExit('Could not find "characters" => %[ block in envinit.tjs')

    # Track depth for the outer characters %[] block
    depth = 0
    # Initialize depth entering the block line
    opens, closes = count_tokens(lines[start_idx])
    depth += opens - closes

    i = start_idx + 1
    while i < len(lines) and depth > 0:
        line = lines[i]
        # Detect a character entry start when inside characters (depth==1)
        if depth == 1:
            m = re.match(r"\s*\"([^\"]+)\"\s*=>\s*%\[\s*$", line)
            if m:
                char_key = m.group(1)
                # Enter this character block and scan until it closes
                char_depth = 1
                i += 1
                voice_file = None
                voice_name = None
                while i < len(lines) and char_depth > 0:
                    ln = lines[i]
                    # Capture voiceFile / voiceName when seen
                    mf = re.search(r'"voiceFile"\s*=>\s*"([^"]+)"', ln)
                    if mf:
                        voice_file = mf.group(1)
                    mn = re.search(r'"voiceName"\s*=>\s*"([^"]+)"', ln)
                    if mn:
                        voice_name = mn.group(1)

                    o, c = count_tokens(ln)
                    char_depth += o - c
                    i += 1
                # Store even if missing; keep None as empty string
                results.append((char_key, voice_name or "", voice_file or ""))
                # Continue without increment here because we've already advanced i
                continue
        # Maintain outer depth
        o, c = count_tokens(line)
        depth += o - c
        i += 1

    return results
