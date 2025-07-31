import os
import json
import argparse
from glob import glob
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn)

columns = (SpinnerColumn(), BarColumn(bar_width=100), "[progress.percentage]{task.percentage:.2f}%", TimeElapsedColumn(), "•", TimeRemainingColumn(), TextColumn("[bold blue]{task.description}"))

LANGUAGE_MAP = {
    "CHS": "zh",
    "CHT": "zh-Hant",
    "EN": "en",
    "JA": "ja-JP"
    }

SOUND_LANG_MAP = {
    "CHS": "Chinese(PRC)",
    "CHT": "Chinese(PRC)",
    "EN":  "English(US)",
    "JA":  "Japanese"
    }

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_path", type=str, default=r"D:\Reverse\_Unreal Engine\FModel\Output\Exports\X6Game\Content")
    parser.add_argument("--language",   type=str, default="CHS", choices=list(LANGUAGE_MAP.keys()))
    return parser.parse_args(args=args, namespace=namespace)

def load_localization(root_path, lang_code):
    folder_lang = LANGUAGE_MAP[lang_code]
    base_loc = {}

    game_json_path = os.path.join(root_path, 'Localization', 'Game', folder_lang, 'Game.json')
    if os.path.isfile(game_json_path):
        with open(game_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 扁平化
        for group, kv in data.items():
            if isinstance(kv, dict):
                for k, v in kv.items():
                    base_loc[k] = v

    # 补丁路径 Patch_001, Patch_002, ...
    patch_root = os.path.join(root_path, 'Localization')
    idx = 1
    while True:
        patch_dir = f"Patch_{idx:03d}"
        patch_json_path = os.path.join(patch_root, patch_dir, folder_lang, f"{patch_dir}.json")
        if not os.path.isfile(patch_json_path):
            break
        with open(patch_json_path, 'r', encoding='utf-8') as f:
            patch_data = json.load(f)
        for group, kv in patch_data.items():
            if isinstance(kv, dict):
                for k, v in kv.items():
                    # 后加载的补丁覆盖主路径和前面补丁
                    base_loc[k] = v
        idx += 1

    return base_loc

def load_voice_dict(root_path, lang_code):
    sb_map = SOUND_LANG_MAP.get(lang_code)
    info_path = os.path.join(root_path, 'Audio', 'SoundbanksInfo.json')

    with open(info_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    voice_dict = {}
    banks = data.get('SoundBanksInfo', {}).get('SoundBanks', [])
    for bank in banks:
        if bank.get('Language') != sb_map:
            continue
        short = bank.get('ShortName')
        media_list = bank.get('Media', [])
        paths = [m.get('Path') for m in media_list if m.get('Path')]
        if short and paths:
            voice_dict[short] = paths
    return voice_dict

def load_dialogues(root_path):
    dialogue_dir = os.path.join(root_path, 'Assets', 'Dialogue')
    pattern = os.path.join(dialogue_dir, '**', '*.json')
    files = glob(pattern, recursive=True)
    entries = []

    with Progress(*columns, transient=True) as progress:
        task = progress.add_task("Processing dialogues", total=len(files))
        for fpath in files:
            progress.update(task, description=os.path.relpath(fpath, root_path))
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nodes = data if isinstance(data, list) else [data]
            for node in nodes:
                if node.get('Type') != 'PaperDialogue':
                    continue
                props = node.get('Properties', {})
                lines = props.get('Lines') or props.get('lines') or []
                for line in lines:
                    speaker = line.get('Speaker', {})
                    actor = speaker.get('ActorName')
                    actor = actor.replace('.', '_') if actor else None

                    text_id = speaker.get('StringID')
                    text_id = 'LDLG_Text_ZH_' + text_id if text_id else None

                    audio = speaker.get('DialogueAudio', {})
                    audio_event = audio.get('AudioEvent')

                    if actor and text_id and audio_event:
                        voice_path = audio_event.get('ObjectPath')
                        if voice_path:
                            entries.append({'Speaker': actor, 'Text': text_id, 'Voice': voice_path})
            progress.advance(task)

    return entries

if __name__ == '__main__':
    args = parse_args()

    loc_map = load_localization(args.root_path, args.language)
    print(f"Loaded {len(loc_map)} localization entries for {args.language}")

    voice_dict = load_voice_dict(args.root_path, args.language)
    print(f"Loaded {len(voice_dict)} voice entries for {args.language}")

    dlg_entries = load_dialogues(args.root_path)
    print(f"Loaded {len(dlg_entries)} dialogue entries")

    processed = []
    for entry in dlg_entries:
        speaker = entry['Speaker']
        text_id = entry['Text']
        text = loc_map.get(text_id, "")
        voice_key = entry['Voice'].split('/')[-1]
        voice_key = voice_key.replace('.0', '')
        voice_paths = voice_dict.get(voice_key, [])
        processed.append({
            'Speaker': speaker,
            'Text': text,
            'Voice': voice_paths
        })

    output_file = os.path.join(args.root_path, f"processed_dialogues_{args.language}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    print(f"Saved processed dialogues to {output_file}")