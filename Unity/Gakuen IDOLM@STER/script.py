import json, re, os

BRACKET_RE = re.compile(r'^\[(\w+)\s*(.*)]$')

def unescape_braces(s: str) -> str:
    return s.replace(r'\{', '{').replace(r'\}', '}').replace(r'\[', '[').replace(r'\]', ']')

def smart_split(s: str):
    parts, buf, depth = [], [], 0
    for ch in s:
        if ch == ' ' and depth == 0:
            if buf:
                parts.append(''.join(buf))
                buf = []
        else:
            buf.append(ch)
            if ch in '[{':
                depth += 1
            elif ch in ']}':
                depth -= 1
    if buf:
        parts.append(''.join(buf))
    return parts

def parse_value(raw: str):
    raw = unescape_braces(raw)
    if raw.startswith('{') and raw.endswith('}'):
        try:
            return json.loads(raw)
        except:
            return raw
    if raw.startswith('[') and raw.endswith(']'):
        # 把最外层 [] 剥掉后按内部分项继续解析
        inner = raw[1:-1].strip()
        if not inner: return []
        items = []
        # 粗分：第一层级的 ' item … ]' 组
        cur, depth = [], 0
        for ch in inner:
            cur.append(ch)
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
            if depth == 0 and ch == ']':
                items.append(''.join(cur))
                cur = []
        return [parse_line(item) for item in items]
    return raw

def parse_line(line: str):
    m = BRACKET_RE.match(line.strip())
    if not m: return {}
    cmd, body = m.groups()
    out = {'cmd': cmd}
    if not body: return out
    for field in smart_split(body):
        if '=' not in field:
            out.setdefault('flags', []).append(field)
            continue
        k, v = field.split('=', 1)
        out[k] = parse_value(v)
    return out

if __name__ == '__main__':
    in_dir = r"D:\Dataset_Game\com.bandainamcoent.idolmaster_gakuen\RAW\m_adventure"
    for item in os.listdir(in_dir):
        if not item.endswith('.txt'):
            continue
        with open(os.path.join(in_dir, item), 'r', encoding='utf-8') as f:
            try:
                lines = f.readlines()
            except:
                continue

        result = []
        for line in lines:
            is_msg = False
            line = parse_line(line)
            if line['cmd'] == 'message':
                Text = line['text']
                is_msg = True
                
            elif line['cmd'] == 'voice' and is_msg:
                pass

            elif line['cmd'] == 'messgae' and is_msg:
                is_msg = False