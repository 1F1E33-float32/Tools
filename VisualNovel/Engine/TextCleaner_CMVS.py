import re
import json
import struct
import argparse
from glob import glob
from tqdm import tqdm

def parse_args(args=None, namespace=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-JA", type=str, default=r"E:\Dataset\FuckGalGame\Purple software\Hapymaher -Fragmentation Dream- RE\script")
    parser.add_argument("-op", type=str, default=r'D:\AI\Audio_Tools\python\1.json')
    return parser.parse_args(args=args, namespace=namespace)

def text_cleaning(text):
    text = re.sub(r"\{([^\s/]+)/[^\s/]+\}", r"\1", text)
    text = text.replace('『', '').replace('』', '').replace('「', '').replace('」', '').replace('（', '').replace('）', '')
    text = text.replace('\\n', '').replace('\\t', '')
    return text

def lzss(CompressData, CompressSize):
    curbyte = 0
    flag = 0
    cur_winpos = 0x7df
    window = [0]*2048
    DeCompressData = []
    while True:
        flag >>= 1
        if not (flag & 0x0100):
            if curbyte >= CompressSize:
                break
            flag = CompressData[curbyte] | 0xff00
            curbyte += 1
        if (flag & 1):
            if curbyte >= CompressSize:
                break
            data = CompressData[curbyte]
            window[cur_winpos] = data
            DeCompressData.append(data)
            curbyte += 1
            cur_winpos = (cur_winpos + 1) & 0x7ff
        else:
            if curbyte >= CompressSize:
                break
            offset = CompressData[curbyte]
            curbyte += 1
            if curbyte >= CompressSize:
                break
            count = CompressData[curbyte]
            curbyte += 1
            offset |= (count & 0xe0) << 3
            count = (count & 0x1f) + 2
            for i in range(count):
                data = window[(offset + i) & 0x7ff]
                DeCompressData.append(data)
                window[cur_winpos] = data
                cur_winpos = (cur_winpos + 1) & 0x7ff
    return DeCompressData

# 0 PS2A 4 HeadSize 8 Unknown 12 SeedKey 16 LabelCount 20 CodeSegSize 24 Unknown 28 TextSegSize 32 BegPC 36 CompressSize 40 DeCompressSize 44 Unknown 48 CompressData......
def main(JA_dir, op_json):
    filelist = glob(f"{JA_dir}/**/*.ps3", recursive=True)
    results = []
    for filename in tqdm(filelist):
        with open(filename, 'rb') as f:
            header = f.read(4).decode()
            if header != 'PS2A':
                raise ValueError('Invalid file header')
            HeadSize, Unknown0, SeedKey, LabelCount, CodeSegSize, UnknownSegSize, TextSegSize, BegPC, CompressSize, DeCompressSize, Unknown2 = struct.unpack('<11I', f.read(44))
            CompressData = bytearray(f.read(CompressSize))

            xor = ((SeedKey >> 24) + (SeedKey >> 3)) & 0xFF
            shifts = ((SeedKey >> 20) % 5) + 1

            for i in range(CompressSize):
                tmp = ((CompressData[i] - 0x7c) & 0xFF) ^ xor
                CompressData[i] = ((tmp >> shifts) | (tmp << (8 - shifts))) & 0xFF
            lzss_data = bytearray(lzss(CompressData, CompressSize))

            label_table_offset = 0
            code_seg_offset = LabelCount * 4
            unkonw_offset = code_seg_offset + CodeSegSize
            text_seg_offset = unkonw_offset + UnknownSegSize
            
            tmp_result = []
            is_speaker = False
            for i in range(len(lzss_data)):
                command_bytes = lzss_data[i:i+4]
                if command_bytes == b'\x01\x02\x20\x01':
                    if i + 8 < len(lzss_data):
                        offset_bytes = lzss_data[i+4:i+8]
                        check_bytes = lzss_data[i+8:i+12]
                        if check_bytes == b'\x0f\x02\x30\x04':
                            offset = struct.unpack('<I', offset_bytes)[0]
                            text_ptr = text_seg_offset + offset
                            Text = []
                            while lzss_data[text_ptr] != 0x00:
                                Text.append(lzss_data[text_ptr])
                                text_ptr += 1
                            tmp_result.append(bytes(Text).decode('cp932'))
                            if is_speaker:
                                try:
                                    Speaker = tmp_result[-1]
                                    Voice = tmp_result[-2]
                                    Text = tmp_result[-3]
                                    substrings = ['.ogg', '.wav', '.mv2', '.pb3', '.pb2', '.ps3', '.ps2', '.cur', '.cmv', '.mgv']
                                    if all(sub not in Speaker for sub in substrings) and all(sub not in Text for sub in substrings) and ".ogg" in Voice:
                                        Text = text_cleaning(Text)
                                        Speaker_id = re.findall(r'^[a-zA-Z]+', Voice)[0]
                                        Speaker = Speaker.replace('　', '').replace('？', '')
                                        if not Speaker:
                                            continue
                                        results.append((Speaker, Speaker_id, Voice, Text))
                                        tmp_result = []
                                        is_speaker = False
                                except:
                                    tmp_result = []
                                    is_speaker = False

                            if tmp_result is not None and len(tmp_result) > 0:
                                if ".ogg" in tmp_result[-1]:
                                    is_speaker = True
                        else:
                            continue
                else:
                    continue

    replace_dict = {}
    for Speaker, Speaker_id, Voice, Text in tqdm(results):
        if Speaker != '？？？' and Speaker_id not in replace_dict:
            replace_dict[Speaker_id] = Speaker

    fixed_results = []
    for Speaker, Speaker_id, Voice, Text in tqdm(results):
        if Speaker == '？？？' and Speaker_id in replace_dict:
            fixed_results.append((replace_dict[Speaker_id], Speaker_id, Voice, Text))
        else:
            fixed_results.append((Speaker, Speaker_id, Voice, Text))

    with open(op_json, mode='w', encoding='utf-8') as file:
        seen = set()
        json_data = []
        for Speaker, Speaker_id, Voice, Text in fixed_results:
            if (Speaker, Speaker_id, Voice, Text) not in seen:
                seen.add((Speaker, Speaker_id, Voice, Text))
                json_data.append({'Speaker': Speaker, 'Voice': Voice, 'Text': Text})
        json.dump(json_data, file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    args = parse_args()
    main(args.JA, args.op)