import argparse
from pathlib import Path

from parser import wparser
from tqdm import tqdm


def banks_to_dict_list(banks):
    return [node_to_dict(node) for node in banks]


def node_to_dict(node):
    if hasattr(node, "_NodeField__name"):
        key = node._NodeField__name
        value = node._NodeField__value
        return {key: value}

    if hasattr(node, "_NodeRoot__filename"):
        key = node._NodeRoot__filename
    elif hasattr(node, "_NodeObject__name"):
        key = node._NodeObject__name
    elif hasattr(node, "_NodeList__name"):
        key = node._NodeList__name
    else:
        raise ValueError(f"Unrecognized node type: {node}")

    children = getattr(node, "_children", []) or []

    children_dicts = [node_to_dict(child) for child in children]

    merged = {}
    for cd in children_dicts:
        for k, v in cd.items():
            if k in merged:
                if not isinstance(merged[k], list):
                    merged[k] = [merged[k]]
                merged[k].append(v)
            else:
                merged[k] = v

    return {key: merged}


def normalize_list(item):
    if isinstance(item, list):
        return item
    elif isinstance(item, dict):
        return [item]
    else:
        return []


def build_event_media_map(bank_dict):
    media_headers = bank_dict["MediaIndex"]["pLoadedMedia"]["MediaHeader"]
    hirc_items = bank_dict["HircChunk"]["listLoadedItem"]
    sounds = hirc_items.get("CAkSound", [])
    actions = hirc_items.get("CAkActionPlay", [])
    events = hirc_items.get("CAkEvent", [])

    #   A. MediaHeader:  sourceID ➜ {uOffset, uSize}
    media_map = {md["id"]: {"uOffset": md["uOffset"], "uSize": md["uSize"]} for md in normalize_list(media_headers)}

    #   B. Sound:  sound_ulID ➜ sourceID
    sound_map = {}
    for snd in normalize_list(sounds):
        source_id = snd["SoundInitialValues"]["AkBankSourceData"]["AkMediaInformation"]["sourceID"]
        sound_map[snd["ulID"]] = source_id

    #   C. Action: action_ulID ➜ idExt(=sound_ulID)
    action_map = {}
    for act in normalize_list(actions):
        action_map[act["ulID"]] = act["ActionInitialValues"]["idExt"]

    result = {}

    def extract_action_ids(action_block):
        if action_block is None:
            return []

        if isinstance(action_block, list):
            return [item.get("Action", item).get("ulActionID") for item in action_block if isinstance(item, (dict,)) and ("Action" in item or "ulActionID" in item)]

        if isinstance(action_block, dict):
            act_field = action_block.get("Action", action_block)
            if isinstance(act_field, list):
                return [x.get("ulActionID") for x in act_field if "ulActionID" in x]
            elif isinstance(act_field, dict):
                return [act_field.get("ulActionID")] if "ulActionID" in act_field else []

        return []

    for evt in normalize_list(events):
        evt_id = evt.get("ulID")
        if evt_id is None:
            continue

        # 取出它引用的 Action ID 列表
        actions_block = evt["EventInitialValues"]["actions"] if "EventInitialValues" in evt else None
        for act_id in extract_action_ids(actions_block):
            sound_ulid = action_map.get(act_id)
            if sound_ulid is None:
                continue

            source_id = sound_map.get(sound_ulid)
            if source_id is None:
                continue

            media_info = media_map.get(source_id)
            if media_info is None:
                continue

            result[evt_id] = media_info
            break  # 同一个事件有多动作时，只取第一条命中的

    return result


def extract_all_wems(bnk_paths, out_root="./output_wems"):
    parser = wparser.Parser()
    parser.parse_banks(bnk_paths)
    banks = parser.get_banks()

    banks_dicts = banks_to_dict_list(banks)

    bank_info = {}
    for entry in tqdm(banks_dicts, ncols=150):
        for name, bd in entry.items():
            media_index = bd.get("MediaIndex", {})
            if media_index == {}:
                continue
            bank_info[name] = {"dwChunkSize": media_index["dwChunkSize"], "events": build_event_media_map(bd)}

    out_root = Path(out_root)
    out_root.mkdir(exist_ok=True)
    name2path = {Path(p).name: Path(p) for p in bnk_paths}

    for name, info in tqdm(bank_info.items(), ncols=150):
        src_path = name2path.get(name)
        if not src_path or not src_path.exists():
            print(f"⚠️ 跳过，找不到源文件 {name}")
            continue

        data = src_path.read_bytes()
        didx = data.find(b"DIDX")
        if didx < 0:
            print(f"⚠️ {name} 无 DIDX，跳过")
            continue

        base = didx + 8 + info["dwChunkSize"]
        if data[base : base + 4] != b"DATA":
            print(f"⚠️ {name} DIDX 后非 DATA，跳过")
            continue
        data_start = base + 8

        odir = out_root / name.replace(".bnk", "")
        odir.mkdir(exist_ok=True)

        for evt_id, mm in info["events"].items():
            start = data_start + mm["uOffset"]
            wem = data[start : start + mm["uSize"]]
            (odir / f"{evt_id}.wem").write_bytes(wem)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bnk_root", default=Path(r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\Android\audios\Android"), help="Root folder containing language subfolders with .bnk files")
    parser.add_argument("--out_root", default=Path(r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\audios\Android"), help="Output root for extracted WEMs organized by language")
    args = parser.parse_args()

    languages = ["zh", "kr", "en", "jp"]
    for lang in languages:
        bnk_folder = args.bnk_root / lang
        out_folder = args.out_root / lang
        out_folder.mkdir(parents=True, exist_ok=True)

        bnk_files = list(bnk_folder.rglob("*.bnk"))
        if not bnk_files:
            print(f"No .bnk files found in {bnk_folder}")
            continue

        print(f"Processing language '{lang}' with {len(bnk_files)} files...")
        extract_all_wems([str(p) for p in bnk_files], out_root=str(out_folder))
        print(f"Finished processing {lang}. Outputs in {out_folder}")
