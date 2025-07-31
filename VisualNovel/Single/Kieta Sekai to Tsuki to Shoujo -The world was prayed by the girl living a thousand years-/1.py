import urllib.parse

def decode_tyrano(encoded_str: str) -> str:
    if encoded_str and encoded_str[0] != '/':
        textwk = ''.join(chr(159 - ord(c)) for c in encoded_str)
        return urllib.parse.unquote(textwk)
    return encoded_str

def make_tag(src: str, line: int, state: dict) -> dict:
    obj = {'line': line, 'name': '', 'pm': {}, 'val': src}
    flag_q = ''
    tmp = ''
    cnt_in_q = 0
    for ch in src:
        if not flag_q and ch in ('"', "'"):
            flag_q = ch; cnt_in_q = 0
        elif flag_q:
            if ch == flag_q:
                flag_q = ''
                if cnt_in_q == 0:
                    tmp += 'undefined'
                cnt_in_q = 0
            else:
                tmp += ('' if ch == ' ' else ('#' if ch == '=' else ch))
                cnt_in_q += 1
        else:
            tmp += ch
    tokens = [t for t in tmp.split(' ') if t]
    if not tokens:
        return obj
    obj['name'] = tokens[0].strip()

    # emulate the funky “= gluing” logic
    t = tokens[:]
    k = 1
    while k < len(t):
        ahead = t[k]
        if ahead == '=' and k + 1 < len(t):
            t[k - 1] += '=' + t[k + 1]; t[k:k + 2] = []
        elif ahead.startswith('='):
            t[k - 1] += ahead; t.pop(k)
        elif ahead.endswith('=') and k + 1 < len(t):
            t[k] += t[k + 1]; t.pop(k + 1)
        else:
            k += 1

    for item in t[1:]:
        if '=' in item:
            key, val = item.split('=', 1)
            if key == '*':
                obj['pm']['*'] = ''
            val = val.replace('#', '=')
            if val == 'undefined':
                val = ''
            obj['pm'][key] = val

    n = obj['name']
    if n == 'if':
        state['deep_if'] += 1; obj['pm']['deep_if'] = state['deep_if']
    elif n in ('elsif', 'else'):
        obj['pm']['deep_if'] = state['deep_if']
    elif n == 'endif':
        obj['pm']['deep_if'] = state['deep_if']; state['deep_if'] -= 1

    if n == 'iscript':
        state['flag_script'] = True
    if n == 'endscript':
        state['flag_script'] = False
    return obj

def parse_ks(txt: str) -> dict:
    arr, labels = [], {}
    st = {'flag_script': False, 'deep_if': 0}
    in_block_comment = False

    for i, raw in enumerate(txt.splitlines()):
        line = raw.strip()
        if 'endscript' in line:
            st['flag_script'] = False
        if in_block_comment and line == '*/':
            in_block_comment = False; continue
        if line == '/*':
            in_block_comment = True; continue
        if in_block_comment or (line.startswith(';')):
            continue
        if not line:
            continue

        head = line[0]

        # 1. character voice/text lines
        if head == '#':
            body = line[1:].strip()
            name, face = (body.split(':', 1) + [''])[:2] if ':' in body else (body, '')
            arr.append({'line': i, 'name': 'chara_ptext', 'pm': {'name': name, 'face': face}, 'val': ''})

        # 2. label lines (*label|visible name)
        elif head == '*':
            key, val = (line[1:].split('|') + [''])[:2]
            lbl = {'name': 'label', 'pm': {'line': i, 'index': len(arr), 'label_name': key.strip(), 'val': val.strip()}, 'val': val.strip()}
            arr.append(lbl); labels.setdefault(key.strip(), lbl['pm'])

        # 3. command lines starting with @
        elif head == '@':
            arr.append(make_tag(line[1:], i, st))

        # 4. plain text w/ inline [tags]
        else:
            row = line[1:] if head == '_' else line
            if '[ruby' in row:
                row = '[ruby text=\'_\']' + row

            buf, tag, depth, in_tag = '', '', 0, False
            for ch in row:
                if in_tag:
                    if ch == ']' and not st['flag_script']:
                        depth -= 1
                        if depth == 0:
                            arr.append(make_tag(tag, i, st)); tag = ''; in_tag = False
                        else:
                            tag += ch
                    elif ch == '[' and not st['flag_script']:
                        depth += 1; tag += ch
                    else:
                        tag += ch
                else:
                    if ch == '[' and not st['flag_script']:
                        depth += 1
                        if buf:
                            arr.append({'line': i, 'name': 'text', 'pm': {'val': buf}, 'val': buf})
                            buf = ''
                        in_tag = True
                    else:
                        buf += ch
            if buf:
                arr.append({'line': i, 'name': 'text', 'pm': {'val': buf}, 'val': buf})

    return {'array_s': arr, 'map_label': labels}

if __name__ == '__main__':
    with open(r"D:\GAL\2018_03\Kieta Sekai to Tsuki to Shoujo -The world was prayed by the girl living a thousand years-\data\scenario\tuki-anzu-day02.ks", 'r', encoding='utf-8') as f:
        encoded = f.read()
    decoded = decode_tyrano(encoded)
    parsed = parse_ks(decoded)
    pass