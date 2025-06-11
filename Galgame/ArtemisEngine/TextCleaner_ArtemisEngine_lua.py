import re, json, argparse
from glob import glob
from lupa import lua_type
from lupa.lua54 import LuaRuntime

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    p.add_argument("-op", type=str, default=r"D:\Fuck_galgame\index.json")
    p.add_argument("-fv", type=int, default=2)
    return p.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r'\[ruby text="[^"]*"\](.*?)\[/ruby\]', r'\1', text)
    text = text.replace('\n', '').replace('\\n', '')
    text = text.replace('」', '').replace('「', '').replace('（', '').replace('）', '').replace('『', '').replace('』', '')
    text = text.replace('●', '').replace('　', '')
    return text

def lua_2_python(obj):
    if lua_type(obj) != 'table':
        return obj

    keys = list(obj.keys())
    if all(isinstance(k, int) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
        return [lua_2_python(obj[i]) for i in range(1, len(keys) + 1)]

    return {k: lua_2_python(v) for k, v in obj.items()}

def process_v0(filename, lua, results):
    with open(filename, 'r', encoding='utf-8') as f:
        data = 'scenario = {}\n' + f.read()
    try:
        lua.execute(data)
        python_dict = lua_2_python(lua.globals().scenario)
    except Exception:
        print(f"Error parsing {filename}")
        return

    for value in python_dict.values():
        for block in value:
            if not isinstance(block, dict):
                continue
            text = block.get("text", [None])[0]
            if text:
                text = text_cleaning(text)
            speaker = voice = None
            for tag in block.get("tag", []):
                if len(tag) == 3 and tag.get(1) == "name":
                    tmp_speaker = re.findall(r"[A-Za-z]+_[A-Za-z]+_\d+", tag["1"])
                    speakers = ['_'.join(t.rsplit('_', 1)[:-1]) or t for t in tmp_speaker]
                    speaker = '&'.join(speakers)
                    voice = tag["1"]
                    break
            if text and speaker and voice:
                results.append({'Speaker': speaker, 'Voice': voice, 'Text': text})

def process_v1(filename, lua, results):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    try:
        lua.execute(data)
        python_dict = lua_2_python(lua.globals().ast)
    except Exception:
        print(f"Error parsing {filename}")
        return

    for value in python_dict.values():
        for block in value.values():
            if not isinstance(block, dict):
                continue
            vo = block.get("vo", [None])[0]
            if not vo:
                continue
            speaker, voice = vo['ch'], vo['file']

            text_block = block.get("ja", [None])[0]
            if not text_block:
                continue
            if isinstance(text_block, dict):
                filtered = {k: v for k, v in text_block.items() if isinstance(k, int)}
                text = ''.join(v for k, v in sorted(filtered.items()) if isinstance(v, str))
            else:  # list
                text = ''.join(i for i in text_block if isinstance(i, str))
            text = text_cleaning(text)
            results.append({'Speaker': speaker, 'Voice': voice, 'Text': text})

def process_v2(filename, lua, results):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    lua.execute(data)
    python_dict = lua_2_python(lua.globals().ast)
    python_dict = dict(sorted(python_dict.items(), key=lambda kv: kv[0]))

    for value in python_dict.values():
        Speaker = Voice = Text = None
        if not isinstance(value, dict):
            continue
        text = value.get("text")
        if text:
            text_block = text["ja"][0]
            if isinstance(text_block, dict):
                Text = ''.join(v for v in (text_block.values() if isinstance(text_block, dict) else text_block) if isinstance(v, str))
            elif isinstance(text_block, list):
                Text = ''.join(i for i in text_block if isinstance(i, str))
            else:
                raise ValueError(f"Unexpected type for text_block: {type(text_block)}")
            Text = text_cleaning(Text)

            vo = text.get("vo")
            if vo:
                Speaker = vo[0]['ch']
                Voice = vo[0]['file']
            
            results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
            

def main(JA_dir, op_json, force_version):
    lua = LuaRuntime(unpack_returned_tuples=True)
    processors = {0: process_v0, 1: process_v1, 2: process_v2}
    if force_version not in processors:
        raise ValueError(f"Unsupported version: {force_version}")

    files = glob(f"{JA_dir}/**/*.ast", recursive=True) + glob(f"{JA_dir}/**/*.lua", recursive=True)
    results = []

    for scene_idx, fn in enumerate(files):
        print(fn)
        start = len(results)
        processors[force_version](fn, lua, results)

        for line_idx, item in enumerate(results[start:], 0):
            item['scene'] = scene_idx
            item['line'] = line_idx

    with open(op_json, 'w', encoding='utf-8') as fp:
        json.dump(results, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    a = parse_args()
    main(a.JA, a.op, a.fv)