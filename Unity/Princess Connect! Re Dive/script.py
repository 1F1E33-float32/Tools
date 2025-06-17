import json
import base64
import argparse
from enum import Enum
from pathlib import Path
from struct import unpack_from
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)

columns = (SpinnerColumn(), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:.2f}%", TimeElapsedColumn(), "•", TimeRemainingColumn(), TextColumn("[bold blue]{task.description}"))

def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\EXP\Story"))
    parser.add_argument("--output", type=Path, default=Path(r"index.json"))
    args = parser.parse_args()
    return args

class CommandId(Enum):
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
    MAX = 110
    UNKNOWN = 112

def clean_text(text):
    text = text.replace("「", "").replace("」", "").replace("『", "").replace("』", "").replace("【", "").replace("】", "")
    text = text.replace("\\n", "\n").replace("\n", "").replace('\\"', '"')
    text = text.replace("\u3000", "")
    return text

def decode_argument(arg):
    inverted = bytes((255 - b) if b > 127 else b for b in arg)
    return base64.b64decode(inverted).decode()

def deserialize_command(raw_command):
    command_id = CommandId(raw_command[0])
    decoded_args = [decode_argument(arg) for arg in raw_command[1:]]
    return command_id, decoded_args

def deserialize_story(data):
    offset = 0
    raw_commands = []

    while offset < len(data):
        if offset + 2 > len(data):
            break

        command_index = unpack_from(">H", data, offset)[0]
        offset += 2
        args = [command_index]

        # Each argument begins with its 4‑byte length; a length of 0 marks the end
        while True:
            if offset + 4 > len(data):
                break
            length = unpack_from(">l", data, offset)[0]
            offset += 4
            if length == 0:
                break
            arg_bytes = data[offset : offset + length]
            offset += length
            args.append(arg_bytes)

        raw_commands.append(args)

    return [deserialize_command(cmd) for cmd in raw_commands if len(cmd) > 1]

def main(data):
    commands = deserialize_story(data)
    blocks = {0: {}}
    current_block = 0

    for command_id, args in commands:
        match command_id:
            case CommandId.PRINT:
                entry = blocks[current_block].setdefault("print", {})
                entry.setdefault("name", args[0])
                entry["text"] = entry.get("text", "") + clean_text(args[1])

            case CommandId.CHOICE:
                choices = blocks[current_block].setdefault("choice", [])
                choices.append({"text": args[0], "tag": args[1]})

            case CommandId.BUSTUP:
                current_block += 1
                blocks.setdefault(current_block, {})

            case CommandId.TAG:
                blocks.setdefault(current_block + 1, {})
                blocks[current_block + 1]["tag"] = args[0]

            case (CommandId.TITLE | CommandId.SITUATION | CommandId.OUTLINE | CommandId.VO | CommandId.GOTO):
                key = command_id.name.lower()
                blocks[current_block][key] = args[0] if len(args) == 1 else args

            case _:
                continue

    return blocks

if __name__ == "__main__":
    args = args_parser()
    result = []
    scene = 0

    input_dir = args.input
    all_bytes = list(input_dir.rglob("*.bytes"))

    with Progress(*columns) as progress:
        task = progress.add_task("", total=len(all_bytes))
        for bytes_path in all_bytes:
            progress.update(task, description=f"{bytes_path.name}", advance=1)

            data = bytes_path.read_bytes()
            story_dict = deserialize_story(data)
            story_json = main(data)

            line = 0
            for block in story_json.values():
                voice = block.get("vo")
                if not voice:
                    continue
                speaker = block["print"]["name"]
                text    = block["print"]["text"]
                if '{0}' in text:
                    continue
                result.append({
                    "Speaker": speaker,
                    "Voice":   voice,
                    "Text":    text,
                    "scene":   scene,
                    "line":    line
                })
                line += 1
            scene += 1

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_json, encoding="utf-8")
    print(f"Written {len(result)} records to {args.output}")