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

def process_type0(filename, lua, results):
    pass

def process_type1(filename, lua, results):
    pass

def process_type2(filename, lua, results):
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
            
            if Speaker and Voice and Text:
                results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
            
PROCESSORS = {0: process_type0, 1: process_type1, 2: process_type2}
def main(JA_dir, op_json, force_version):
    lua = LuaRuntime(unpack_returned_tuples=True)
    if force_version not in PROCESSORS:
        raise ValueError(f"Unsupported version: {force_version}")

    files = glob(f"{JA_dir}/**/*.ast", recursive=True) + glob(f"{JA_dir}/**/*.lua", recursive=True)
    results = []

    for fn in files:
        print(fn)
        PROCESSORS[force_version](fn, lua, results)

    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)

    with open(op_json, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    a = parse_args()
    main(a.JA, a.op, a.fv)