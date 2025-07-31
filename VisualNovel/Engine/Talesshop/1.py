import xml.etree.ElementTree as ET
from collections import defaultdict
import json

def xml_to_dict(xml_string: str) -> dict:
    def _element_to_dict(elem: ET.Element):
        node = {}
        if elem.attrib:
            node["@attributes"] = dict(elem.attrib)
        # 递归子节点
        child_nodes = defaultdict(list)
        for child in elem:
            child_dict = _element_to_dict(child)
            child_nodes[child.tag].append(child_dict)
        for tag, child_list in child_nodes.items():
            node[tag] = child_list if len(child_list) > 1 else child_list[0]
        # 文本节点
        text = (elem.text or "").strip()
        if text:
            return text if not node else {**node, "#text": text}
        return node

    root = ET.fromstring(xml_string)
    return {root.tag: _element_to_dict(root)}

def ensure_list(x):
    if isinstance(x, list):
        return x
    return [x]

def parse_dict(data):
    results = []
    ucscript = data.get('ucscript', {})
    scenes = ucscript.get('scene', [])
    for scene in ensure_list(scenes):
        nodes = scene.get('node', [])
        for node in ensure_list(nodes):
            inst = node.get('inst', {})
            raw_page = inst.get('page', [])
            pages = ensure_list(raw_page)
            for page in pages:
                Voice = None
                comment = page.get('@attributes', {}).get('comment')
                if comment != '' and comment is not None:
                    parts = comment.split(';')
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue

                        if len(part) > 1 and part.startswith('@'):
                                key, value = part[1:].replace(' ', '').split('=', 1)
                                Voice = f"{key}_{value}"
                                break
                if Voice:
                    text_data = delay_temp = None
                    try:
                        text_data = page.get('content', {}).get('text', {}).get('@attributes', {}).get('data')
                    except KeyError:
                        delay_temp = page.get('delay', {}).get('@attributes', {}).get('temp')
                    content = text_data if text_data is not None else delay_temp
                    if content is None:
                        continue
                    parts = content.split(';')
                    if len(parts) < 2:
                        continue
                    Speaker = parts[0]
                    Text = ''.join(parts[1:])
                    Speaker = Speaker.replace('#t=', '')
                    Speaker = Speaker.replace('?', '？')
                    results.append({
                        "Speaker": Speaker,
                        "Voice":   Voice,
                        "Text":    Text
                    })
                    Voice = Speaker = Text = None
    return results

if __name__ == "__main__":
    with open(r"D:\GAL\#KR\Some Some Pyeonuijeom\ex\some\script", "r", encoding='utf-8') as f:
        data = f.read()

    xml_dict = xml_to_dict(data)
    results = parse_dict(xml_dict)
    seen = set()
    unique_results = []
    for entry in results:
        v = entry.get("Voice")
        if v and v not in seen:
            seen.add(v)
            unique_results.append(entry)
    results = unique_results

    with open(r"D:\Fuck_galgame\index.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
