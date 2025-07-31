import os
import av
import json
import shutil
import argparse
from tqdm import tqdm

from MSM1 import build_voice_maps as build_voice_maps_msm1, resolve_audio_path as resolve_audio_path_msm1
from MSM2 import build_voice_maps as build_voice_maps_msm2, resolve_audio_path as resolve_audio_path_msm2
from TWD import build_voice_maps as build_voice_maps_twd, resolve_audio_path as resolve_audio_path_twd

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("--root_dir",   default=r"D:\VMware\steamapps\common\The Walking Dead The Telltale Definitive Series\fsb5_dec")
    p.add_argument("--index_json", default=r"D:\Fuck_galgame\index.json")
    p.add_argument("--out_dir",    default=r"D:\Dataset_VN_NoScene\#OK L\TWD")
    p.add_argument("--audio_ext",  default=".ogg")
    p.add_argument("--game",       default="TWD", choices=["MSM1", "MSM2", "TWD"])
    return p.parse_args(args=args, namespace=namespace)

def get_audio_duration(path: str) -> float:
    container = av.open(path, metadata_errors="ignore")
    if container.duration is not None:
        return container.duration / 1_000_000
    max_t = 0.0
    for frame in container.decode(audio=0):
        if frame.time and frame.time > max_t:
            max_t = frame.time
    return max_t

def build_dataset(index_path, root_dir, out_dir, audio_ext, game):
    # Select the appropriate voice map builder and resolver based on game code
    match game:
        case "MSM1":
            build_voice_maps = build_voice_maps_msm1
            resolve_audio_path = resolve_audio_path_msm1
        case "MSM2":
            build_voice_maps = build_voice_maps_msm2
            resolve_audio_path = resolve_audio_path_msm2
        case "TWD":
            build_voice_maps = build_voice_maps_twd
            resolve_audio_path = resolve_audio_path_twd
        case _:
            raise ValueError(f"Unsupported game code: {game}")

    female_maps, male_maps = build_voice_maps(root_dir, audio_ext)

    with open(index_path, encoding="utf-8") as fp:
        records = json.load(fp)

    new_entries = []
    missing = 0

    for rec in tqdm(records, desc="Filtering records", ncols=120):
        id_     = rec.get("id")
        speaker = rec.get("Speaker")
        wav_id  = rec.get("Voice")

        if not id_ or not speaker or not wav_id:
            missing += 1
            continue

        audio_path = resolve_audio_path(id_, speaker, wav_id, female_maps, male_maps)
        if not audio_path or not os.path.isfile(audio_path):
            print(f"Skipping, audio not found: ID={id_}, Speaker={speaker}, Voice={wav_id}")
            missing += 1
            continue

        try:
            duration = get_audio_duration(audio_path)
        except Exception as e:
            print(f"Skipping, invalid audio: {audio_path}, error: {e}")
            missing += 1
            continue

        base = os.path.basename(audio_path)
        new_name = f"{id_}_{base}"
        entry = {
            "Speaker": speaker,
            "Voice": new_name,
            "Text": rec.get("Text", "")
        }
        new_entries.append((entry, audio_path))

    print(f"Valid records: {len(new_entries)}, Discarded: {missing}")

    # Copy audio files
    for entry, src in tqdm(new_entries, desc="Copying audio", ncols=120):
        speaker = entry["Speaker"]
        voice   = entry["Voice"]
        dst_dir = os.path.join(out_dir, speaker)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, voice)
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            print(f"Copy failed: {src} -> {dst}: {e}")

    # Write new index.json without id field
    os.makedirs(out_dir, exist_ok=True)
    index_out = os.path.join(out_dir, "index.json")
    with open(index_out, "w", encoding="utf-8") as fp:
        json.dump([e for e, _ in new_entries], fp, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    args = parse_args()
    build_dataset(
        index_path=args.index_json,
        root_dir=args.root_dir,
        out_dir=args.out_dir,
        audio_ext=args.audio_ext,
        game=args.game
    )
