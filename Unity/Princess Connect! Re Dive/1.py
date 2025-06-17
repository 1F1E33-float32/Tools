from __future__ import annotations

import base64
import io
from enum import IntEnum
from typing import List, Dict, Any


# --------------------------------------------------------------------------- #
#  Enums                                                                      #
# --------------------------------------------------------------------------- #
class CommandNumber(IntEnum):
    NONE = -1
    TITLE = 0
    OUTLINE = 1
    VISIBLE = 2
    FACE = 3
    FOCUS = 4
    BACKGROUND = 5
    PRINT = 6
    TAG = 7
    GOTO = 8
    BGM = 9
    TOUCH = 10
    CHOICE = 11
    VO = 12
    WAIT = 13
    IN_L = 14
    IN_R = 15
    OUT_L = 16
    OUT_R = 17
    FADEIN = 18
    FADEOUT = 19
    IN_FLOAT = 20
    OUT_FLOAT = 21
    JUMP = 22
    SHAKE = 23
    POP = 24
    NOD = 25
    SE = 26
    BLACK_OUT = 27
    BLACK_IN = 28
    WHITE_OUT = 29
    WHITE_IN = 30
    TRANSITION = 31
    SITUATION = 32
    COLOR_FADEIN = 33
    FLASH = 34
    SHAKE_TEXT = 35
    TEXT_SIZE = 36
    SHAKE_SCREEN = 37
    DOUBLE = 38
    SCALE = 39
    TITLE_TELOP = 40
    WINDOW_VISIBLE = 41
    LOG = 42
    NOVOICE = 43
    CHANGE = 44
    FADEOUT_ALL = 45
    MOVIE = 46
    MOVIE_STAY = 47
    BATTLE = 48
    STILL = 49
    BUSTUP = 50
    ENV = 51
    TUTORIAL_REWARD = 52
    NAME_EDIT = 53
    EFFECT = 54
    EFFECT_DELETE = 55
    EYE_OPEN = 56
    MOUTH_OPEN = 57
    AUTO_END = 58
    EMOTION = 59
    EMOTION_END = 60
    ENV_STOP = 61
    BGM_PAUSE = 62
    BGM_RESUME = 63
    BGM_VOLUME_CHANGE = 64
    ENV_RESUME = 65
    ENV_VOLUME = 66
    SE_PAUSE = 67
    CHARA_FULL = 68
    SWAY = 69
    BACKGROUND_COLOR = 70
    PAN = 71
    STILL_UNIT = 72
    SLIDE_CHARA = 73
    SHAKE_SCREEN_ONCE = 74
    TRANSITION_RESUME = 75
    SHAKE_LOOP = 76
    SHAKE_DELETE = 77
    UNFACE = 78
    WAIT_TOKEN = 79
    EFFECT_ENV = 80
    BRIGHT_CHANGE = 81
    CHARA_SHADOW = 82
    UI_VISIBLE = 83
    FADEIN_ALL = 84
    CHANGE_WINDOW = 85
    BG_PAN = 86
    STILL_MOVE = 87
    STILL_NORMALIZE = 88
    VOICE_EFFECT = 89
    TRIAL_END = 90
    SE_EFFECT = 91
    CHARACTER_UP_DOWN = 92
    BG_CAMERA_ZOOM = 93
    BACKGROUND_SPLIT = 94
    CAMERA_ZOOM = 95
    SPLIT_SLIDE = 96
    BGM_TRANSITION = 97
    SHAKE_ANIME = 98
    INSERT_STORY = 99
    PLACE = 100
    IGNORE_BGM = 101
    MULTI_LIPSYNC = 102
    JINGLE = 103
    TOUCH_TO_START = 104
    EVENT_ADV_MOVE_HORIZONTAL = 105
    BG_PAN_X = 106
    BACKGROUND_BLUR = 107
    SEASONAL_REWARD = 108
    MINI_GAME = 109


class CommandCategory(IntEnum):
    Non = 0
    System = 1
    Motion = 2
    Effect = 3


# --------------------------------------------------------------------------- #
#  Quick lookup tables (index == command number)                              #
# --------------------------------------------------------------------------- #
# Only the fields actually used below are stored (Name & Category)
_COMMAND_NAMES: List[str | None] = [
    # 0 - 109
    "title", "outline", "visible", "face", "focus", "background", "print",
    "tag", "goto", "bgm", "touch", "choice", "vo", "wait", "in_L", "in_R",
    "out_L", "out_R", "fadein", "fadeout", "in_float", "out_float", "jump",
    "shake", "pop", "nod", "se", "black_out", "black_in", "white_out",
    "white_in", "transition", "situation", "color_fadein", "flash",
    "shake_text", "text_size", "shake_screen", "double", "scale",
    "title_telop", "window_visible", "log", "novoice", "change",
    "fadeout_all", "movie", "movie_stay", "battle", "still", "bust",
    "amb", "reward", "name_dialog", "effect", "effect_delete", "eye_open",
    "mouth_open", "end", "emotion", "emotion_end", "amb_stop", "bgm_stop",
    "bgm_resume", "bgm_volume", "amb_resume", "amb_volume", "se_pause",
    "chara_full", "sway", "bg_color", "pan", "still_unit", "slide",
    "shake_once", "transition_resume", "shake_loop", "shake_delete",
    "unface", "token", "effect_env", "bright_change", "chara_shadow",
    "ui_visible", "fadein_all", "change_window", "bg_pan", "still_move",
    "still_normalize", "vo_effect", "trial_end", "se_effect", "updown",
    "bg_zoom", "split", "camera_zoom", "split_slide", "bgm_transition",
    "shake_anime", "insert", "place", "bgm_overview", "multi_talk",
    "jingle_start", "touch_to_start", "event_change", "bg_pan_slide",
    "bg_blur", "seasonal_reward", "mini_game"
]

# category is only informational – not used anywhere except being forwarded
_COMMAND_CATEGORIES: List[int] = [
    CommandCategory.System,   # title
    CommandCategory.System,   # outline
    CommandCategory.System,   # …
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Motion,   # in_L
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.System,   # se
    CommandCategory.System,   # black_out
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Motion,   # scale
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Motion,
    CommandCategory.Motion,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Effect,
    CommandCategory.Effect,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Effect,
    CommandCategory.Effect,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Motion,
    CommandCategory.System,   # sway
    CommandCategory.System,   # bg_color
    CommandCategory.Motion,   # pan
    CommandCategory.System,   # still_unit
    CommandCategory.Motion,   # slide
    CommandCategory.System,   # shake_once
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Effect,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.Motion,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System,
    CommandCategory.System
]


# --------------------------------------------------------------------------- #
#  Tiny in-memory stream helper (read & write)                                #
# --------------------------------------------------------------------------- #
class MemoryStream:
    def __init__(self, data: bytes | bytearray = b"") -> None:
        self._buf = io.BytesIO(data)

    # --- Reading helpers --------------------------------------------------- #
    def read(self, size: int = -1) -> bytes:
        return self._buf.read(size)

    def read_short(self) -> int:
        return int.from_bytes(self._buf.read(2), "little", signed=False)

    def read_long(self) -> int:
        return int.from_bytes(self._buf.read(4), "little", signed=False)

    def read_data(self, size: int) -> bytes:
        return self._buf.read(size)

    # --- Writing helpers --------------------------------------------------- #
    def write(self, data: str | bytes | bytearray) -> None:
        if isinstance(data, str):
            data = data.encode()
        self._buf.write(data)

    # --- Properties -------------------------------------------------------- #
    @property
    def size(self) -> int:
        current = self._buf.tell()
        self._buf.seek(0, io.SEEK_END)
        size = self._buf.tell()
        self._buf.seek(current)
        return size

    @property
    def position(self) -> int:
        return self._buf.tell()

    @position.setter
    def position(self, pos: int) -> None:
        self._buf.seek(pos)


# --------------------------------------------------------------------------- #
#  Deserializer                                                               #
# --------------------------------------------------------------------------- #
class RediveStoryDeserializer:
    """Parse Re:Dive story binary and (optionally) build the same HTML preview
    the original PHP produced."""

    def __init__(self, blob: bytes) -> None:
        self.command_list: List[Dict[str, Any]] = self._parse(blob)
        self.html: str = self._build_html()

    # --------------------------------------------------------------------- #
    #  Core parsing loop                                                    #
    # --------------------------------------------------------------------- #
    def _parse(self, data: bytes) -> List[Dict[str, Any]]:
        fs = MemoryStream(data)

        # The binary starts with an unused 16-bit field → skip
        _ = fs.read_short()

        lines: List[List[bytes | int]] = []
        while fs.position < fs.size:
            idx = fs.read_short()
            line: List[bytes | int] = [idx]

            while True:
                length = fs.read_long()
                if length == 0:
                    break

                line.append(fs.read_data(length))

            lines.append(line)

        return [
            self._deserialize_line(line)
            for line in lines
            if self._get_command_name(line[0]) is not None
        ]

    # --------------------------------------------------------------------- #
    #  Helpers                                                              #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _convert_string_arg(raw: bytes) -> str:
        """Reverse the simple obfuscation then base64-decode + cleanup."""
        buf = bytearray(raw)
        for i in range(0, len(buf), 3):
            buf[i] = 0xFF - buf[i]

        decoded = base64.b64decode(buf).decode("utf-8", errors="replace")
        return decoded.replace(r"\n", "\n").replace("{0}", "{player}")

    @staticmethod
    def _build_face_name(code: int) -> str:
        names = [
            "normal", "normal", "joy", "anger", "sad", "shy", "surprised",
            "special_a", "special_b", "special_c", "special_d", "special_e",
            "default"
        ]
        return names[code] if code < len(names) else f"unknown({code})"

    # --------------------------------------------------------------------- #
    #  Mapping tables                                                       #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _get_command_name(index: int) -> str | None:
        return _COMMAND_NAMES[index] if index < len(_COMMAND_NAMES) else None

    @staticmethod
    def _get_command_category(index: int) -> int | None:
        return _COMMAND_CATEGORIES[index] if index < len(_COMMAND_CATEGORIES) else None

    def _deserialize_line(self, cmd_bytes: List[bytes | int]) -> Dict[str, Any]:
        idx: int = cmd_bytes[0]  # type: ignore[index]
        return {
            "name": self._get_command_name(idx),
            "args": [self._convert_string_arg(arg) for arg in cmd_bytes[1:]],
            "category": self._get_command_category(idx),
            "number": idx,
        }

    # --------------------------------------------------------------------- #
    #  Crude HTML dump (identical to the PHP output)                        #
    # --------------------------------------------------------------------- #
    def _build_html(self) -> str:
        if not self.command_list:
            return ""

        def h(text: str) -> str:
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        out: List[str] = []
        title = h(self.command_list[0]["args"][0]) if self.command_list[0]["args"] else "story"

        out.append(
            f'<!DOCTYPE HTML><html><head><title>{title}</title>'
            '<meta charset="UTF-8" name="viewport" content="width=device-width">'
            '<style>.cmd{color:#DDD;font-size:12px;cursor:pointer}'
            '.highlight{background:#ccc;color:#000}</style></head>'
            '<body style="background:#444;color:#FFF;font-family:Meiryo;'
            '-webkit-text-size-adjust:none;cursor:default"><b>'
        )

        # title & outline lines
        out.append(f'{h(self.command_list[0]["args"][0])}<br>\n')
        if len(self.command_list) > 1 and self.command_list[1]["args"]:
            out.append(f'{h(self.command_list[1]["args"][0])}</b><br>\n<br>\n')

        # running buffer for print/touch blocks
        buf_chara = ""
        buf_text = ""
        current_chara = ""
        current_face = ""

        for cmd in self.command_list:
            name = cmd["name"]
            args = cmd["args"]

            if name == "print":
                buf_chara = h(args[0])
                buf_text += h(args[1]).replace("\n", "<br>\n")
            elif name == "touch":
                out.append(f"{buf_chara}：<br>\n{buf_text}<br>\n<br>\n")
                buf_chara = buf_text = ""
                current_chara = current_face = ""
            elif name == "choice":
                out.append(f'<div>Choice: ({h(args[1])}) {h(args[0])}</div>\n')
            elif name == "tag":
                out.append(f'<div class="cmd">----- Tag {h(args[0])} -----</div>\n')
            elif name == "goto":
                out.append(f'<div class="cmd">Jump to tag {h(args[0])}</div>\n')
            elif name == "vo":
                out.append(f'<div class="voice cmd">voice: {h(args[0])}</div>\n')
            elif name in {"movie", "movie_stay"}:
                out.append(f'<div class="movie cmd">movie: {h(args[0])}</div>\n')
            elif name == "white_out":
                out.append("<b>--- Switch scene ---</b><br>\n<br>\n")
            elif name == "situation":
                out.append(f"-------------- situation: <br>\n<b>{h(args[0])}</b><br>\n--------------<br>\n<br>\n")
            elif name == "place":
                out.append(f"-------------- place: <br>\n<b>{h(args[0])}</b><br>\n--------------<br>\n<br>\n")
            elif name == "face":
                face_name = self._build_face_name(int(args[1]))
                if current_chara == args[0] and current_face == face_name:
                    continue
                current_chara, current_face = args[0], face_name
                out.append(
                    f'<span class="face cmd" data-chara="{h(args[0])}" '
                    f'data-face="{face_name}">【chara {h(args[0])} face {h(args[1])} '
                    f'({face_name})】</span>\n'
                )
            elif name == "still":
                if args[0] == "end":
                    out.append('<div class="cmd">still display end</div>\n')
                else:
                    img = h(args[0])
                    out.append(
                        f'<a href="https://redive.estertion.win/card/story/{img}.webp" target="_blank">'
                        f'<img alt="story_still_{img}" '
                        f'src="https://redive.estertion.win/card/story/{img}.webp@w300"></a><br>\n'
                    )

        out.append('<script src="/static/story_data.min.js"></script></body></html>')
        return "".join(out)


# --------------------------------------------------------------------------- #
#  Minimal CLI for quick testing                                              #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse
    import pathlib

    p = argparse.ArgumentParser(description="Re:Dive story binary → HTML preview")
    p.add_argument("input", type=pathlib.Path, help="binary .bin / .story file")
    p.add_argument("-o", "--output", type=pathlib.Path, help="html output path (default: <input>.html)")

    args = p.parse_args()
    data = args.input.read_bytes()
    deser = RediveStoryDeserializer(data)

    out_path = args.output or args.input.with_suffix(".html")
    out_path.write_text(deser.html, encoding="utf-8")
    print(f"Wrote {out_path}")