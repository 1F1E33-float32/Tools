import re
import json
import enum
import base64
import argparse
from tqdm import tqdm
from typing import List
from glob import glob
from dataclasses import dataclass, field

def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=r"D:\Dataset_Game\jp.co.bandainamcoent.BNEI0242\EXP\Story")
    return parser.parse_args()

class CommandCategory(enum.Enum):
    Non = 0
    System = 1
    Motion = 2
    Effect = 3

@dataclass
class CommandStruct:
    Name: str | None = None
    Args: List[str] = field(default_factory=list)
    Category: CommandCategory = CommandCategory.Non

@dataclass
class CommandConfig:
    ID: int = -1
    Summary: str = ""
    Name: str = ""
    Usage: str = ""
    ClassName: str = ""
    Category: CommandCategory = CommandCategory.Non
    MinArgCount: int = 0
    MaxArgCount: int = 0

class Config:
    def __init__(self):
        self._commandConfigList = []
        self.RegisterCommandConfig("title", "タイトル設定", "title <タイトル名>", "Title", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("outline", "あらすじ設定", "outline <あらすじ>", "Outline", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("chara", "キャラの追加", "chara <キャラID> <L:左, LC:左寄り, C:真ん中, RC:右寄り, R:右> <タイプID> <表情ID>", "Chara", CommandCategory.System, 4, 4)
        self.RegisterCommandConfig("visible", "キャラ表示切り替え", "visible <キャラID> <true か false>", "Visible", CommandCategory.System, 2, 2)
        self.RegisterCommandConfig("type", "キャラタイプ切り替え", "type <キャラID> <タイプID>", "Type", CommandCategory.System, 2, 2)
        self.RegisterCommandConfig("face", "キャラ表情", "face <キャラID> <表情ID> <タイプID:オプション> <オフセットX:オプション> <オフセットY:オプション>", "Face", CommandCategory.System, 2, 5)
        self.RegisterCommandConfig("focus", "キャラを明るく表示", "focus <キャラID>", "Focus", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("background", "背景設定", "background <背景ID もしくは カードID>", "Background", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("print", "テキスト表示", "pring <名前> <テキスト>", "Print", CommandCategory.System, 2, 2)
        self.RegisterCommandConfig("tag", "タグ設定", "tag <タグID>", "Tag", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("goto", "指定タグの位置に移動", "goto <飛ばしたいタグID>", "Goto", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("bgm", "BGM指定", "bgm <キュー名> <stop時のフェードタイムorボリューム>", "Bgm", CommandCategory.System, 1, 2)
        self.RegisterCommandConfig("touch", "タッチ入力待ち", "touch", "Touch", CommandCategory.System, 0, 0)
        self.RegisterCommandConfig("choice", "選択肢追加", "choice <選択肢ラベル> <飛ばしたいタグID>", "Choice", CommandCategory.System, 2, 2)
        self.RegisterCommandConfig("vo", "ボイス再生", "vo <ボイスキュー名>", "Vo", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("wait", "指定時間待機", "wait <待ち時間>", "Wait", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("in_L", "左からスライドイン", "in_L <キャラID> <フレーム数:オプション> <フェードフラグ:オプション>", "InL", CommandCategory.Motion, 1, 3)
        self.RegisterCommandConfig("in_R", "右からスライドイン>", "in_R <キャラID> <フレーム数:オプション> <フェードフラグ:オプション>", "InR", CommandCategory.Motion, 1, 3)
        self.RegisterCommandConfig("out_L", "左へスライドアウト", "out_L <キャラID> <フレーム数:オプション> <フェードフラグ:オプション>", "OutL", CommandCategory.Motion, 1, 3)
        self.RegisterCommandConfig("out_R", "右へスライドアウト", "out_R <キャラID> <フレーム数:オプション> <フェードフラグ:オプション>", "OutR", CommandCategory.Motion, 1, 3)
        self.RegisterCommandConfig("fadein", "フェードイン>", "fadein <キャラID> <フレーム数:オプション>", "Fadein", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("fadeout", "フェードアウト", "fadeout <キャラID> <フレーム数:オプション>", "Fadeout", CommandCategory.Motion, 0, 2)
        self.RegisterCommandConfig("in_float", "フロートイン", "in_float <キャラID> <フレーム数:オプション>", "InFloat", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("out_float", "フロートアウト", "out_float <キャラID> <フレーム数:オプション>", "OutFloat", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("jump", "ジャンプ", "jump <キャラID> <回数:オプション>", "Jump", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("shake", "震える", "shake <キャラID> <回数:オプション>", "Shake", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("pop", "軽く弾む", "pop <キャラID> <回数:オプション>", "Pop", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("nod", "沈む", "nod <キャラID> <回数:オプション>", "Nod", CommandCategory.Motion, 1, 2)
        self.RegisterCommandConfig("question_right", "はてな\u3000右向き", "question_right <キャラID>", "QuestionRight", CommandCategory.Motion, 1, 1)
        self.RegisterCommandConfig("question_left", "はてな\u3000左向き", "question_left <キャラID>", "QuestionLeft", CommandCategory.Motion, 1, 1)
        self.RegisterCommandConfig("se", "SE再生", "se <キューシート> <キュー名>", "Se", CommandCategory.System, 1, 2)
        self.RegisterCommandConfig("black_out", "暗転", "black_out <アルファ:オプション> <時間:オプション>", "BlackOut", CommandCategory.System, 0, 2)
        self.RegisterCommandConfig("black_in", "暗転からの復帰", "black_in", "BlackIn", CommandCategory.System, 0, 2)
        self.RegisterCommandConfig("white_out", "ホワイトアウト", "white_out <アルファ:オプション> <時間:オプション>", "WhiteOut", CommandCategory.System, 0, 2)
        self.RegisterCommandConfig("white_in", "ホワイトアウトから復帰", "white_in", "WhiteIn", CommandCategory.System, 0, 2)
        self.RegisterCommandConfig("transition", "場面転換演出", "transition <アニメ名:オプション>", "Transition", CommandCategory.System, 0, 1)
        self.RegisterCommandConfig("situation", "指定文字列を帯表示", "situation <場面名>", "Situation", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("color_fadein", "指定色フェードイン", "color_fadein <RGBコード> <透明度> <時間>", "ColorFadein", CommandCategory.System, 3, 3)
        self.RegisterCommandConfig("flash", "フラッシュ", "flash", "Flash", CommandCategory.System, 0, 0)
        self.RegisterCommandConfig("shake_text", "テキストウィンドウを揺らす", "shake_text", "ShakeText", CommandCategory.System, 0, 0)
        self.RegisterCommandConfig("text_size", "フォントサイズ指定", "text_size <フォントサイズ>", "TextSize", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("shake_screen", "画面全体揺らす", "shake_screen", "ShakeScreen", CommandCategory.System, 0, 0)
        self.RegisterCommandConfig("double", "テキストを重ねて表示", "double <名前> <テキスト> <オフセットX:オプション> <オフセットY:オプション>", "Double", CommandCategory.System, 2, 4)
        self.RegisterCommandConfig("flower_y", "黄色の花びら", "flower_y <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "FlowerY", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("flower_r", "赤い花びら", "flower_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "FlowerR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("concent", "集中線", "concent <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "Concent", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("find_l", "気付(左)", "find_l <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "FindL", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("find_r", "気付き(右)", "find_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "FindR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("laugh_l", "笑い三本線(左)", "laugh_l <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "LaughL", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("laugh_r", "笑い三本線(右)", "laugh_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "LaughR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("chord_l", "音符(左)", "chord_l <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "ChordL", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("chord_r", "音符(右)", "chord_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "ChordR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("sweat_l", "汗(左)", "sweat_l <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "SweatL", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("sweat_r", "汗(右)", "sweat_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "SweatR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("question_l", "はてな(左)", "question_l <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "QuestionL", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("question_r", "はてな(右)", "question_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "QuestionR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("angry", "ぷんすか(左)", "angry <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "Angry", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("drop_l", "汗2(左)", "drop_l <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "DropL", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("drop_r", "汗2(右)", "drop_r <キャラID> <オフセットX:オプション> <オフセットY:オプション>", "DropR", CommandCategory.Effect, 1, 3)
        self.RegisterCommandConfig("live", "ライブ遷移", "live <楽曲ID> <難易度(debut:1から数字上がる毎に難易度アップ)> <メンバー1ID> <メンバー2ID> <メンバー3ID> <メンバー4ID> <メンバー5ID> <観客フラグ:オプション>", "Live", CommandCategory.System, 7, 8)
        self.RegisterCommandConfig("scale", "拡縮", "scale <キャラID> <拡縮率(等倍は1)>", "Scale", CommandCategory.Motion, 2, 2)
        self.RegisterCommandConfig("title_telop", "タイトルテロップ", "title_telop <ストーリーID>", "TitleTelop", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("window_visible", "テキストウィンドウの表示切り替え", "window_visible <\"true\" か \"false\">", "WindowVisible", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("log", "ログにだけ表示するテキスト", "log <キャラID> <名前> <テキスト> <ボイスID : オプション>", "Log", CommandCategory.System, 3, 4)
        self.RegisterCommandConfig("novoice", "ボイス再生しない", "novoice", "NoVoice", CommandCategory.System, 0, 0)
        self.RegisterCommandConfig("attract", "話している人", "attract <キャラID>", "Attract", CommandCategory.System, 1, 1)
        self.RegisterCommandConfig("change", "キャラ位置入れ替え", "change <位置1> <位置2> <移動フレーム数:オプション>", "Change", CommandCategory.Motion, 2, 3)
        self.RegisterCommandConfig("fadeout_all", "キャラとウィンドウを消す", "fadeout_all <フェード時間(フレーム)>", "FadeoutAll", CommandCategory.System, 0, 1)
        self.RegisterCommandConfig("2dlive_info", "2Dのコミュライブ時用のユニット情報設定", "2dlive_info  <メンバー1ID> <メンバー2ID> <メンバー3ID> <メンバー4ID> <メンバー5ID>", "TwoDLiveInfo", CommandCategory.System, 5, 5)
        self.RegisterCommandConfig("3dlive_info", "3Dのコミュライブ時用のユニット情報設定", "3dlive_info  <メンバー1ID> <メンバー2ID> <メンバー3ID> <メンバー4ID> <メンバー5ID>", "ThreeDLiveInfo", CommandCategory.System, 5, 5)
        self.RegisterCommandConfig("fl_anim", "Flashアニメーション再生", "fl_anim", "FlAnim", CommandCategory.System, 0, 0)
        self.RegisterCommandConfig("live_popup", "LIVE設定ポップアップの表示", "live_popup", "LivePopup", CommandCategory.System, 0, 0)

    def RegisterCommandConfig(self, name, summary, usage, className, category, minArgCount, maxArgCount):
        idx = len(self._commandConfigList)
        cfg = CommandConfig(
            ID=idx - 1,
            Summary=summary,
            Name=name,
            Usage=usage,
            ClassName=className,
            Category=category,
            MinArgCount=minArgCount,
            MaxArgCount=maxArgCount,
        )
        self._commandConfigList.append(cfg)

    def GetCommandID(self, name: str):
        for i, cfg in enumerate(self._commandConfigList):
            if cfg.Name == name:
                return i
        return -1

    def GetCommandName(self, id_: int):
        if 0 <= id_ < len(self._commandConfigList):
            return self._commandConfigList[id_].Name
        return None

    def GetCommandCategory(self, id_: int):
        if 0 <= id_ < len(self._commandConfigList):
            return self._commandConfigList[id_].Category
        return CommandCategory.Non
    
class Parser:
    def __init__(self, data):
        self._binaryFileBuffer = data
        self._binaryFileBufferSize = len(data)
        self._commandList = []
        self._config = Config()
        self._headOnly = re.compile(r'^[\"](.*)')
        self._tailOnly = re.compile(r'(.*)[\"]$')

    def Deserialize(self):
        rows = self.SplitCommandByteRow()
        for row in rows:
            item = self.DeserializeLine(row)
            self._commandList.append(item)
        return self._commandList

    def SplitCommandByteRow(self):
        result = []
        num = 2
        while num < self._binaryFileBufferSize:
            row = []
            first_field = self._binaryFileBuffer[num-2:num][::-1]
            row.append(first_field)

            num2 = num
            while True:
                length = int.from_bytes(self._binaryFileBuffer[num2:num2+4], 'big')
                if length == 0:
                    break
                data = self._binaryFileBuffer[num2+4 : num2+4+length]
                row.append(data)
                num2 += 4 + length

            num = num2 + 4 + 2
            result.append(row)
        return result
    
    def DeserializeLine(self, commandByte: List[bytes]):
        result = CommandStruct(Args=[])
        idx = int.from_bytes(commandByte[0], "little", signed=False)
        result.Name = self.GetCommandName(idx)
        for seg in commandByte[1:]:
            text = self.ConvertStringArgs(seg)
            if text == "se_common":
                text = "se_common_dl"
            result.Args.append(text)
        result.Category = self.GetCommandCategory(idx)
        return result

    def SplitString(self, commandLine: str):
        parts, quote_stack = [], []
        start = 0
        for i, ch in enumerate(commandLine):
            if ch == " " and not quote_stack:
                parts.append(commandLine[start:i])
                start = i + 1
                continue
            if ch == "\"":
                if not quote_stack or quote_stack[-1]:
                    quote_stack.append(True)
                else:
                    quote_stack.pop()
            elif ch == "<":
                parts.append(commandLine[start:i])
                start = i + 1
                parts.append("<")
                quote_stack.append(False)
            elif ch == ">":
                if quote_stack and not quote_stack[-1]:
                    quote_stack.pop()
                inner = commandLine[start:i]
                parts.extend(self.SplitString(inner))
                parts.append("<")
                for token in parts:
                    if token == "<":
                        break
                    parts.append(token)
                parts.pop()
                start = i + 1
        if start < len(commandLine):
            parts.append(commandLine[start:])
        cleaned = []
        for token in parts:
            if token in ("print", "double"):
                # remove following two tokens if empty quotes
                continue
            token = self._headOnly.sub(r"\1", token)
            token = self._tailOnly.sub(r"\1", token)
            if token:
                cleaned.append(token)
        return cleaned

    def ConvertStringArgs(self, byteArgs: bytes):
        ba = bytearray(byteArgs)
        self.BitInverse(ba)
        decoded = base64.b64decode(ba.decode("utf-8"))
        return decoded.decode("utf-8")
        
    def GetCommandName(self, id_: int):
        return self._config.GetCommandName(id_)
    
    def GetCommandCategory(self, id_: int):
        return self._config.GetCommandCategory(id_)

    def BitInverse(self, byteList: bytearray):
        for i in range(0, len(byteList), 3):
            byteList[i] = (~byteList[i]) & 0xFF

if __name__ == "__main__":
    args = args_parse()
    src = args.src
    files = glob(f"{src}/*.bytes", recursive=True)
    results = []
    seen = set()
    for file in tqdm(files, ncols=150):
        with open(file, "rb") as f:
            data = f.read()
            parser = Parser(data)
            commands = parser.Deserialize()

            is_voice = False
            is_start = False
            Voice = None
            Text_accum = ""
            Speaker_temp = None

            for cmd in commands:
                if cmd.Name == "title_telop":
                    story_id = cmd.Args[0]
                    is_start = True

                elif cmd.Name == "vo" and is_start:
                    Voice = int(cmd.Args[0].split("_")[-1]) + 1
                    Voice = f"story_{story_id}_{Voice:03d}"
                    is_voice = True

                    Text_accum = ""
                    Speaker_temp = None

                elif cmd.Name == "print" and is_start and is_voice:
                    if Speaker_temp is None:
                        Speaker_temp = cmd.Args[0]
                        Speaker_temp = Speaker_temp.replace(" ", "").replace("?", "？")
                        if Speaker_temp == "":
                            is_voice = False
                            continue
                    Text_accum += cmd.Args[1]

                elif cmd.Name == "touch" and is_start and is_voice:
                    if Text_accum:
                        if Voice in seen:
                            is_voice = False
                            continue
                        seen.add(Voice)
                        results.append({
                            "Speaker": Speaker_temp,
                            "Voice": Voice,
                            "Text": Text_accum.replace(r"\n", "").replace(" ", "").replace("（", "").replace("）", ""),
                        })
                    is_voice = False

    with open(r"D:\Fuck_galgame\index.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)