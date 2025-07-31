import re, json, argparse
from glob import glob
from lupa import lua_type
from lupa.lua54 import LuaRuntime

def parse_args(args=None, namespace=None):
    p = argparse.ArgumentParser()
    p.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\script")
    p.add_argument("-op", type=str, default=r"D:\Fuck_galgame\index.json")
    p.add_argument("-fv", type=int, default=1)
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
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    lua.execute(data)
    python_dict = lua_2_python(lua.globals().ast)
    text = python_dict.get("text")
    if text:
        for item in text:
            if isinstance(item, dict):
                vo = item.get("vo")
                if vo:
                    Speaker = item.get('name')
                    if Speaker:
                        Speaker = Speaker['name']
                    else:
                        continue
                    Voice = vo[0]['file']
                    Text = ''.join(i for i in item[1] if isinstance(i, str))
                    Text = text_cleaning(Text)
                    
                    if Speaker and Voice and Text:
                        results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})

def process_type1(filename, lua, results):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    lua.execute(data)
    python_dict = lua_2_python(lua.globals().ast)

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

def process_type2(filename, lua, results):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    data = "scenario = {}\n" + data
    lua.execute(data)
    python_dict = lua_2_python(lua.globals().scenario)
    for value in python_dict.values():
        for item in value:
            if len(item) >= 1:
                for tag_name in item['tag']:
                    if isinstance(tag_name, dict) and len(tag_name) >= 3:
                        if tag_name[1] == 'name':
                            Speaker = tag_name['0']
                            Voice = tag_name['1']
                            Text = ''.join(item['text'])
                            Text = text_cleaning(Text)
                            results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})

def process_type3(filename, lua, results):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    lua.execute(data)
    python_dict = lua_2_python(lua.globals().ast)
    for item in python_dict.values():
        finding_text = False
        for entry in item.values():
            if isinstance(entry, dict):
                name = entry.get('name')
                path = entry.get('path')
                voice = entry.get('voice')
                text = entry.get('text')
                file = entry.get('file')
                if name and voice and text and path and file and (not finding_text):
                    Speaker = name
                    Voice = voice
                    Text = text_cleaning(text)
                    results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
                    break
                elif name and voice and path and (not text) and (not file) and (not finding_text):
                    Speaker = name
                    Voice = voice
                    finding_text = True
                elif finding_text and text:
                    Text = text['ja']
                    Text = ''.join(i for i in Text if isinstance(i, str))
                    Text = text_cleaning(Text)
                    results.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
                    finding_text = False


PROCESSORS = {
    0: process_type0,
    1: process_type1,
    2: process_type2,
    3: process_type3,
    }

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