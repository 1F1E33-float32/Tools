import re
import zlib
import json
import struct
import argparse
from glob import glob
from tqdm import tqdm

global pos
pos = 0

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"D:\Fuck_galgame\scene")
    parser.add_argument("-op", type=str, default=r'D:\Fuck_galgame\index.json')
    return parser.parse_args(args=args, namespace=namespace)

def uncompress_cstx(filename):
    CSTXSig = b'CSTX'
    with open(filename, 'rb') as f:
        data = f.read()
    if not data.startswith(CSTXSig):
        raise ValueError("Invalid file signature")
    
    header_format = '<Iiii'  #uint32, int32, int32, int32
    header_size = struct.calcsize(header_format)
    sig, orig_len, compress_len, mode = struct.unpack_from(header_format, data, 0)
    pos = header_size
    left_len = len(data) - pos - compress_len
    
    if mode == 1:
        uncompressed_data = zlib.decompressobj(-zlib.MAX_WBITS).decompress(data[pos:pos + compress_len])
        data = uncompressed_data + data[pos + compress_len:]
    else:
        data = data[pos:pos + orig_len + left_len]
    return data

def read_chunk_num(data):
    global pos
    if len(data) < pos + 4:
        return 0
    else:
        num = data[pos]
        num |= data[pos + 1] << 8
        num |= data[pos + 2] << 16
        num |= data[pos + 3] << 24
        pos += 4
        return num
    
def read_string_num(data):
    global pos
    num = 0
    shift = 0
    while True:
        if shift >= 32:
            raise ValueError("Invalid length")
        byte = data[pos]
        pos += 1
        num |= (byte & 0x7F) << shift
        shift += 7
        if byte < 128:
            return num
        
def read_string(data):
    global pos
    length = read_string_num(data)
    if length == 0:
        return ""
    elif length < 0 or length > len(data[pos:]):
        raise Exception("Read String Error!")
    str = data[pos:pos + length].decode('utf-8')
    pos += length
    return str

def text_cleaning(text):
    text =  re.sub(r'\[([^]/]*)/([^]]*)\]', r'\1', text)
    text =  re.sub(r'\[([^]/]*):([^]]*)\]', r'\1', text)
    text = re.sub(r'\\(?!w0)[a-zA-Z0-9]{2}', '', text)
    text = re.sub(r'\\w0;.*', '', text)
    text = text.replace('」', '').replace('「', '').replace('』', '').replace('『', '').replace('（', '').replace( '）', '')
    text = text.replace('\\@', '').replace('\\n', '').replace('♪', '').replace('　', '').replace('"', '').replace("\t", "")
    return text

def is_desired_string(string):
    undesired_prefixes = (
        "//", "\t//", "%", "#", "\t#", "\t\\n", "\t＠",
        "\tbg", "\tcall", "\tcam", "\tcg", "\tdic_reg", "\teg", "\tepl", "\temoinfo", "\tfg", "\tframe", "\tfw",
        "if", "\tif", "\tmovie", "\tmpl", "particle", "\tparticle", "\tpl", "\trdraw", "\trwipe", "\tse", "\twait", "\twipe"
    )

    undesired_fullstrings = ["", "\t", "\tinitialize_header", "fmpl"]

    undesired_substrings = ["fmpl"]

    undesired_pattern = re.compile(r"\tpcm \d+ end")

    if (
        string.startswith(undesired_prefixes) or
        string in undesired_fullstrings or
        undesired_pattern.match(string) or
        any(substring in string for substring in undesired_substrings)
    ):
        return False
    return True

def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.cstx", recursive=True)
    results = []

    for filename in tqdm(filelist):
        global pos
        pos = 0
        tmp_results = []
        data = uncompress_cstx(filename)
        chunk_num = read_chunk_num(data)
        if chunk_num > 0:
            for i in range(chunk_num):
                string_num = read_string_num(data)
                for j in range(string_num):
                    string = read_string(data)
                    string = string.lstrip(' ')
                    string = string.split('\t//')[0]
                    if is_desired_string(string):
                        tmp_results.append(string)

        with open(filename.replace(".cstx", ".txt"), 'w', encoding='utf-8') as f:
            for line in tmp_results:
                f.write(line + '\n')

        a = 0
        b = 0
        while a < len(tmp_results):
            if tmp_results[a].startswith("\tpcm"):
                tmp_audio = []
                tmp_speaker = []
                for b in range(a, len(tmp_results)):
                    if tmp_results[b].startswith("\tpcm"):
                        tmp_audio.append(tmp_results[b])

                    elif not tmp_results[b].startswith("\t") and tmp_results[b] != "":
                        tmp_speaker = [re.split('＠', part)[0].replace(" ", "") for part in tmp_results[b].split('＆')][:b - a]

                    elif tmp_results[b].startswith("\t") and len(tmp_audio) == len(tmp_speaker):
                        Text = ""
                        while tmp_results[b].startswith("\t「"):
                            Text += tmp_results[b]
                            if '」' in tmp_results[b]:
                                break
                            b += 1
                        while tmp_results[b].startswith("\t『"):
                            Text += tmp_results[b]
                            if '』' in tmp_results[b]:
                                break
                            b += 1
                        break
                    else:
                        print(f"{filename} {tmp_results[b]}")
                        break

                if  len(tmp_audio) == len(tmp_speaker):  
                    for tmp_audio, tmp_speaker in zip(tmp_audio, tmp_speaker):
                        tmp_audio = tmp_audio.replace("\tpcm ", "")
                        Text = text_cleaning(Text)
                        results.append((tmp_speaker, tmp_audio, Text))
                a = b
            a += 1

    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Voice, Text in results:
            if Voice not in seen:
                seen.add(Voice)
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)