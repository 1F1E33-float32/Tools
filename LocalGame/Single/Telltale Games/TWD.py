import os

# 支持的索引：101–106, 201–205, 301–305, 401–404 以及 M101–M103
INDICES = [*map(str, range(101, 107)),
           *map(str, range(201, 206)),
           *map(str, range(301, 306)),
           *map(str, range(401, 405)),
           "M101", "M102", "M103"]

def get_data_dir(root_path: str, index: str) -> str:
    return os.path.join(root_path, f"WDC_pc_WalkingDead{index}_data")

def get_voice_dir(root_path: str, index: str) -> str:
    return os.path.join(root_path, f"WDC_pc_WalkingDead{index}_voice")

def scan_voice_dir(dir_path: str, audio_ext: str) -> dict[str, str]:
    audio_map: dict[str, str] = {}
    if not os.path.isdir(dir_path):
        return audio_map
    ext = audio_ext.lower()
    for root, _, files in os.walk(dir_path):
        for fname in files:
            if fname.lower().endswith(ext):
                key = os.path.splitext(fname)[0].lower()
                audio_map[key] = os.path.join(root, fname)
    return audio_map

def build_voice_maps(root_dir: str, audio_ext: str):
    """
    Returns two dicts:
      female_maps: { index: { wav_key: full_path } }
      male_maps:   { index: { wav_key: full_path } }
    For TWD 场景，male_maps 会一直是空 dict。
    """
    female_maps = {}
    male_maps = {}
    for idx in INDICES:
        vdir = get_voice_dir(root_dir, idx)
        # TWD 不分性别，所有音频都放 female_maps；male_maps 保持空
        female_maps[idx] = scan_voice_dir(vdir, audio_ext)
        male_maps[idx]   = {}  # 保留接口，始终空
    return female_maps, male_maps

def resolve_audio_path(index: str, speaker, wav_id: str | None, female_maps: dict[str, dict[str, str]], male_maps: dict[str, dict[str, str]]) -> str | None:
    """
    根据 index 和 wav_id 在对应映射表中查找音频路径。
    对于 TWD 场景，直接在 female_maps 查找即可。
    """
    if not wav_id:
        return None
    key = os.path.splitext(str(wav_id))[0].lower()
    # MSM1/MSM2 会根据 speaker 决定查 female_maps 还是 male_maps，
    # 但 TWD 场景中 speaker 不分性别，都用 female_maps
    return female_maps.get(index, {}).get(key)