import os

StartId = 201

def get_female_voice_dir(root_path, id_):
    """JESSE_Female + 所有非 JESSE_Male 角色的音频目录。"""
    if id_ == StartId:
        # 根目录下的 MC2_pc_Minecraft{id}_voice
        return os.path.join(root_path, f"MC2_pc_Minecraft{id_}_voice")
    # 子目录 {id_}/MC2_pc_Minecraft{id_}_voice
    return os.path.join(root_path, str(id_), f"MC2_pc_Minecraft{id_}_voice")

def get_male_voice_dir(root_path, id_):
    """JESSE_Male 音频目录。"""
    if id_ == StartId:
        # 根目录下的 MC2_pc_JesseMale{id}_voice
        return os.path.join(root_path, f"MC2_pc_JesseMale{id_}_voice")
    # 子目录 {id_}/MC2_pc_JesseMale{id_}_uncompressed
    return os.path.join(root_path, str(id_), f"MC2_pc_JesseMale{id_}_uncompressed")

def scan_voice_dir(dir_path, audio_ext):
    """
    扫描给定目录，递归收集所有指定扩展名文件。
    返回 dict: {lower_name_no_ext: full_path}
    """
    audio_map = {}
    if not os.path.isdir(dir_path):
        return audio_map
    ext_lower = audio_ext.lower()
    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.lower().endswith(ext_lower):
                key = os.path.splitext(f)[0].lower()
                audio_map.setdefault(key, os.path.join(root, f))
    return audio_map

def build_voice_maps(root_dir, audio_ext):
    """
    为所有 id (StartId..StartId+7) 建立查找表：
    female_voice_maps[id_] = {...}
    male_voice_maps[id_]   = {...}
    """
    female_voice_maps = {}
    male_voice_maps = {}
    for id_ in range(StartId, StartId + 8):
        female_voice_maps[id_] = scan_voice_dir(get_female_voice_dir(root_dir, id_), audio_ext)
        male_voice_maps[id_] = scan_voice_dir(get_male_voice_dir(root_dir, id_), audio_ext)
    return female_voice_maps, male_voice_maps

def resolve_audio_path(id_, speaker, wav_id, female_maps, male_maps):
    """
    根据记录中的 id, speaker, wav_id，从正确的目录映射表中找音频。
    返回 full_path 或 None。
    """
    if not wav_id:
        return None
    key = os.path.splitext(str(wav_id))[0].lower()
    if speaker and speaker.lower() == 'jesse_male':
        return male_maps.get(id_, {}).get(key)
    return female_maps.get(id_, {}).get(key)
