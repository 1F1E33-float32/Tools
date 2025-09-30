import argparse
import io
import json
import os
import pathlib
import re
from typing import Dict, List, Tuple

from parsec_envinit import parse_envinit_characters


def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_VN\scenario")
    parser.add_argument("-op", type=str, default=r"D:\Fuck_VN\index.json")
    parser.add_argument("-tjs_root", type=str, default=r"D:\Fuck_VN\data")
    return parser.parse_args(args=args, namespace=namespace)


def text_cleaning(text):
    text = re.sub(r"^【[^】]*】\s*", "", text)
    text = text.replace("『", "").replace("』", "").replace("「", "").replace("」", "").replace("（", "").replace("）", "")
    text = text.replace("　", "").replace("／", "")
    return text


def is_comment_or_empty(line: str) -> bool:
    ls = line.strip()
    return (not ls) or ls.startswith(";")


def load_mapping(tjs_root: str) -> Dict[str, str]:
    envinit_path = os.path.join(tjs_root, "envinit.tjs")
    with io.open(envinit_path, "r", encoding="cp932", errors="ignore") as ef:
        env_text = ef.read()
    mapping = parse_envinit_characters(env_text)
    return mapping


def main(JA_dir: str, op_json: str, tjs_root: str):
    mapping = load_mapping(tjs_root)
    results: List[Tuple[str, str, str]] = []

    ks_dir = pathlib.Path(JA_dir)
    files = [p for p in ks_dir.rglob("*.ks") if p.is_file()]

    # Full-line tag regexes (include brackets)
    voicebase_line_re = re.compile(r"^\[\s*eval\s+exp\s*=\s*['\"]\s*f\.voiceBase\s*=\s*\"?(\d+)\"?\s*['\"]\s*\]\s*$")
    tag_voice_name_form_re = re.compile(r"^\[[^\]]*?\bname\s*=\s*['\"]([^'\"]+)['\"][^\]]*?\bvoice\s*=\s*(\d+)[^\]]*\]\s*$")
    tag_voice_leading_speaker_re = re.compile(r"^\[\s*([^\s\]=]+)[^\]]*?\bvoice\s*=\s*(\d+)[^\]]*\]\s*$")
    name_label_re = re.compile(r"^【([^】]+)】(.*)$")
    dispname_line_re = re.compile(r"^\[\s*dispname\b[^\]]*?\bname\s*=\s*(?:[\"']?)([^\"'\]]+)(?:[\"']?)[^\]]*\](.*)$")

    for path in files:
        with io.open(str(path), "r", encoding="cp932", errors="ignore") as f:
            lines = f.readlines()

        # Per-file globals
        speaker_num: Dict[str, int] = {}
        voice_base: str = ""

        for raw in lines:
            line = raw.rstrip("\n\r")
            stripped = line.strip()

            # Skip comments
            if not stripped or stripped.startswith(";"):
                continue

            # [eval exp='f.voiceBase="110"']
            mvb_line = voicebase_line_re.match(stripped)
            if mvb_line:
                voice_base = mvb_line.group(1)
                continue

            # [voice name=Speaker voice=number]
            m_name_form = tag_voice_name_form_re.match(stripped)
            if m_name_form:
                speaker_raw = m_name_form.group(1)
                vnum = int(m_name_form.group(2))
                core = re.split(r"[／/]", speaker_raw)[0].strip()
                key = core.split()[0] if core else speaker_raw
                speaker_num[key] = vnum
                continue

            # [Speaker voice=number]
            m_leading = tag_voice_leading_speaker_re.match(stripped)
            if m_leading:
                speaker_raw = m_leading.group(1)
                vnum = int(m_leading.group(2))
                core = re.split(r"[／/]", speaker_raw)[0].strip()
                key = core.split()[0] if core else speaker_raw
                speaker_num[key] = vnum
                continue

            # Dialogue line: [dispname name=Speaker]Text
            mdisp = dispname_line_re.match(line)
            if mdisp:
                raw_speaker = mdisp.group(1).strip()
                text = text_cleaning(mdisp.group(2))

                core = re.split(r"[／/]", raw_speaker)[0].strip()
                speaker = core.split()[0] if core else raw_speaker

                if speaker not in speaker_num:
                    speaker_num[speaker] = 1

                voice_file_tpl = mapping.get(speaker) or mapping.get(speaker.replace(" ", ""))
                if not voice_file_tpl:
                    continue

                num = speaker_num[speaker]
                voice_str = voice_file_tpl % (voice_base, num)
                if voice_str:
                    results.append((speaker, voice_str, text))
                    speaker_num[speaker] = num + 1
                continue

            # Dialogue line: 【Speaker】Text
            mline = name_label_re.match(line)
            if not mline:
                continue

            raw_speaker = mline.group(1).strip()
            text = text_cleaning(line)

            # normalize
            core = re.split(r"[／/]", raw_speaker)[0].strip()
            speaker = core.split()[0] if core else raw_speaker

            # default starting number = 1 if not set
            if speaker not in speaker_num:
                speaker_num[speaker] = 1

            # resolve template
            voice_file_tpl = mapping.get(speaker) or mapping.get(speaker.replace(" ", ""))
            if not voice_file_tpl:
                continue

            num = speaker_num[speaker]
            voice_str = voice_file_tpl % (voice_base, num)
            if voice_str:
                results.append((speaker, voice_str, text))
                speaker_num[speaker] = num + 1

    # Deduplicate by Voice
    seen = set()
    json_data = []
    for Speaker, Voice, Text in results:
        if Voice not in seen:
            seen.add(Voice)
            json_data.append({"Speaker": Speaker, "Voice": Voice, "Text": Text})

    with open(op_json, mode="w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    main(args.JA, args.op, args.tjs_root)
