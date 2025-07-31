from enum import Enum

class EscapeType(Enum):
    NONE = 0
    NEW_LINE = 1
    PAUSE = 2
    FONT_SIZE = 3
    FONT_COLOR = 4
    TEXT_DISP_SPEED = 5
    TEXT_FADE_TIME = 6
    TEXT_CENTER = 7
    VOICE_VOLUME = 8
    WAIT = 9
    VOICE_WAIT = 10
    VOICE = 11
    FACE_TYPE = 12
    RUBY = 13
    NO_KEY_WAIT = 14
    NO_KEY_WAIT_E = 15
    FORCE_AUTO = 16
    GAIJI = 17
    TEXT_NO_DISP = 18
    VOICE_OVER_PLAY = 19
    ESCAPE = 20

class NeXAS_MessageData:
    escape_dictionary = {
        "@n": EscapeType.NEW_LINE,
        "@p": EscapeType.PAUSE,
        "@s": EscapeType.FONT_SIZE,
        "@i": EscapeType.FONT_COLOR,
        "@m": EscapeType.TEXT_DISP_SPEED,
        "@f": EscapeType.TEXT_FADE_TIME,
        "@c": EscapeType.TEXT_CENTER,
        "@o": EscapeType.VOICE_VOLUME,
        "@w": EscapeType.WAIT,
        "@t": EscapeType.VOICE_WAIT,
        "@v": EscapeType.VOICE,
        "@h": EscapeType.FACE_TYPE,
        "@r": EscapeType.RUBY,
        "@k": EscapeType.NO_KEY_WAIT,
        "@e": EscapeType.NO_KEY_WAIT_E,
        "@a": EscapeType.FORCE_AUTO,
        "@g": EscapeType.GAIJI,
        "@d": EscapeType.TEXT_NO_DISP,
        "@l": EscapeType.VOICE_OVER_PLAY,
        "@@": EscapeType.ESCAPE,

        '@H': EscapeType.FACE_TYPE,
        '@j': EscapeType.FACE_TYPE,

    }

    def __init__(self):
        self.escape = EscapeType.NONE  # 转义类型
        self.row = 0                   # 行号
        self.index = 0                 # 当前行中字符位置
        self.text = ""                 # 文本内容
        self.command = ""              # 附加命令字符串

    def __repr__(self):
        return (f"<MsgData escape={self.escape.name}, row={self.row}, index={self.index}, text='{self.text}', command='{self.command}'>")


def text_analyze(text: str):
    disp_message = ""
    in_quotes = False                 # 是否处于「或『之间
    allow_autoline = True             # 是否允许自动换行插入指令
    auto_line_break_triggered = False
    escape_type = EscapeType.NONE
    current_data = None

    row = 0          # 当前行号
    idx = 0          # 当前行中字符位置计数
    ruby_count = 0   # 用于 RUBY 模式时计数遇到的 '@'
    char_count = 0   # 当前行中已输出的字符数，用于判断自动换行
    line_num = 1     # 总行数
    result = []      # 保存所有的 NeXAS_MessageData 对象

    while len(text) > 0:
        # 检查是否为转义码（至少2个字符）且当前未处于转义处理状态
        if escape_type == EscapeType.NONE and len(text) >= 2:
            potential_escape = text[:2]
            if potential_escape in NeXAS_MessageData.escape_dictionary:
                escape_type = NeXAS_MessageData.escape_dictionary[potential_escape]
                if escape_type == EscapeType.NEW_LINE and not auto_line_break_triggered:
                    allow_autoline = False
                ruby_count = 0
                current_data = NeXAS_MessageData()
                current_data.escape = escape_type
                current_data.row = row
                current_data.index = idx
                result.append(current_data)
                text = text[2:]
                continue

        if escape_type == EscapeType.NONE:
            if len(text) <= 0:
                break
            ch = text[0]
            disp_message += ch  # 只追加文字内容
            text = text[1:]
            new_data = NeXAS_MessageData()
            new_data.escape = EscapeType.NONE
            new_data.row = row
            new_data.index = idx
            new_data.text = ch
            result.append(new_data)
            idx += 1

            if not in_quotes:
                if ch in ["「", "『"]:
                    in_quotes = True
            else:
                if ch in ["」", "』"]:
                    in_quotes = False

            # 自动换行判断：原逻辑会插入换行指令 "@n"，现仅调整内部计数，不修改 disp_message
            if allow_autoline:
                char_count += 1
                if (char_count >= 27 and ch not in ["」", "』", "。", "，", "！", "？", "…", "—"] and len(text) >= 1 and text[0] not in ["」", "』", "。", "，", "！", "？", "…", "—"]):
                    # text = "@n" + text
                    char_count = 0
                    line_num += 1
                    auto_line_break_triggered = True
            continue

        else:
            if escape_type == EscapeType.NEW_LINE:
                row += 1
                idx = 0
                if in_quotes:
                    new_data = NeXAS_MessageData()
                    new_data.escape = EscapeType.NONE
                    new_data.row = row
                    new_data.index = idx
                    new_data.text = "\u3000"
                    result.append(new_data)
                # disp_message += "\n"
                # if in_quotes:
                #     disp_message += "\u3000"
                if not allow_autoline:
                    line_num += 1
                escape_type = EscapeType.NONE
                continue

            # 针对只起控制作用、无需输出文字的转义码
            elif escape_type in [EscapeType.PAUSE, EscapeType.TEXT_CENTER, EscapeType.NO_KEY_WAIT, EscapeType.NO_KEY_WAIT_E, EscapeType.FORCE_AUTO, EscapeType.TEXT_NO_DISP, EscapeType.VOICE_OVER_PLAY]:
                escape_type = EscapeType.NONE
                continue

            # VOICE 和 FACE_TYPE 模式：只允许 ASCII 数字、英文字母和下划线作为命令字符
            elif escape_type in [EscapeType.VOICE, EscapeType.FACE_TYPE]:
                allowed_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"
                while len(text) > 0:
                    ch = text[0]
                    if ch not in allowed_chars:
                        break
                    current_data.command += ch
                    text = text[1:]
                escape_type = EscapeType.NONE
                continue

            # RUBY 模式：区分正文（写入 disp_message 与当前数据）和命令（追加到 command 中）
            elif escape_type == EscapeType.RUBY:
                while len(text) > 0:
                    ch = text[0]
                    text = text[1:]
                    if ch == "@":
                        ruby_count += 1
                        if ruby_count >= 2:
                            break
                    elif ruby_count == 0:
                        current_data.text += ch
                        disp_message += ch
                        idx += 1
                        if not in_quotes:
                            if ch in ["「", "『"]:
                                in_quotes = True
                        else:
                            if ch in ["」", "』"]:
                                in_quotes = False
                    else:
                        current_data.command += ch
                escape_type = EscapeType.NONE
                continue

            # ESCAPE 模式：将 "@@" 显示成 "@"
            elif escape_type == EscapeType.ESCAPE:
                new_data = NeXAS_MessageData()
                new_data.escape = EscapeType.NONE
                new_data.text = "@"
                result.append(new_data)
                escape_type = EscapeType.NONE
                continue

            # 其它情况：读取连续数字作为命令
            else:
                while len(text) > 0:
                    ch = text[0]
                    if not ch.isdigit():
                        break
                    current_data.command += ch
                    text = text[1:]
                escape_type = EscapeType.NONE
                continue

    return result, disp_message