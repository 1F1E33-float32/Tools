import argparse
import json
import re
from typing import List, Tuple


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\script\newgame.ks")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text: str) -> str:
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("\n", "").replace("\\", "")
    return text


_CMD_BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
_CMD_ATLINE_RE = re.compile(r"(?m)^\s*@([A-Za-z_]+)([^\r\n]*)")
_PARAM_RE = re.compile(r'(\w+)=(".*?"|\'.*?\'|\S+)')

_COMMENT_LINE_RE = re.compile(r"(?m)^[ \t]*;.*$")


def _strip_comment_lines(text: str) -> str:
    return _COMMENT_LINE_RE.sub("", text)


def _to_bracket_commands(text: str) -> str:
    def repl(m: re.Match) -> str:
        cmd = m.group(1)
        rest = (m.group(2) or "").strip()
        if rest:
            return f"[{cmd} {rest}]"
        return f"[{cmd}]"

    return _CMD_ATLINE_RE.sub(repl, text)


def _parse_command(cmd_str: str) -> Tuple[str, dict]:
    cmd_str = cmd_str.strip()
    if not cmd_str:
        return "", {}

    # 命令名 = 第一个 token（直到空格）
    parts = cmd_str.split(None, 1)
    name = parts[0].upper()
    params_str = parts[1] if len(parts) > 1 else ""

    params = {}
    for k, v in _PARAM_RE.findall(params_str):
        # 去掉引号
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        params[k.upper()] = v
    return name, params


def _apply_ruby_replacements(text: str, rubies: List[Tuple[str, str]]) -> str:
    for kanji, ruby in rubies:
        if kanji:
            text = text.replace(kanji, ruby)
    return text


def extract_speaker_voice_text(content: str) -> List[Tuple[str, str, str]]:
    content = _strip_comment_lines(content)
    content = _to_bracket_commands(content)

    results: List[Tuple[str, str, str]] = []
    speaker = ""
    voice = ""
    buf_text = ""
    pending_rubies: List[Tuple[str, str]] = []

    idx = 0
    for m in _CMD_BRACKET_RE.finditer(content):
        segment = content[idx : m.start()]
        if segment:
            buf_text += segment

        cmd_raw = m.group(1)
        cmd, params = _parse_command(cmd_raw)

        if cmd in ("NAME_M", "NAME_W"):
            # 说话人
            if "N" in params:
                speaker = params["N"]

        elif cmd == "VO":
            # 语音文件
            if "VO" in params:
                voice = params["VO"]

        elif cmd in ("L", "P", "L_NEXT", "T_NEXT"):
            # 提交一条台词
            text = _apply_ruby_replacements(buf_text, pending_rubies)
            text = text.replace("\r", "")
            text = text_cleaning(text).strip()
            if speaker and voice and text:
                results.append((speaker, voice, text))
            # 重置缓冲
            buf_text = ""
            pending_rubies.clear()
            voice = ""  # 通常一条台词对应一次 VO，提交后清空

        elif cmd == "R":
            # 换行
            buf_text += "\n"

        elif cmd == "CH":
            # 内联文本 [ch text=...]
            t = params.get("TEXT")
            if t:
                buf_text += t

        elif cmd == "RUBY":
            ruby = params.get("TEXT", "")
            kanji = params.get("KANJI", "")
            if ruby:
                pending_rubies.append((kanji, ruby))

        elif cmd in ("ER", "CM", "CT"):
            buf_text = ""
            pending_rubies.clear()

        elif cmd in ("NAME_TIPS_OFF",):
            speaker = None

        idx = m.end()

    if buf_text.strip():
        text = _apply_ruby_replacements(buf_text, pending_rubies)
        text = text_cleaning(text)
        if speaker and voice and text:
            results.append((speaker, voice, text))

    return results


def main(JA_file, op_json):
    with open(JA_file, "r", encoding="utf-8") as f:
        content = f.read()

    results = extract_speaker_voice_text(content)

    seen = set()
    json_data = []
    for Speaker, Voice, Text in results:
        if Voice not in seen:
            seen.add(Voice)
            json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})

    with open(op_json, mode="w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op)
