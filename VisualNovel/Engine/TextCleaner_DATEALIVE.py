import re
import os
from glob import glob

def match_audio(line):
    return re.findall(r'"(.*?)"', line)

def match_speaker(line):
    return re.findall(r"\((.*?)\)", line)

def match_text(line):
    return re.findall(r'"(.*?)"', line)

def main(file_path, output_dir, debug_mode=False):
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines]

    results = []
    for i, line in enumerate(lines):
        if 'MesTitle' in line:
            speaker = match_speaker(line)[0]
            speaker = speaker.replace('CHAR_', '')

            if i + 1 < len(lines) and 'PlayVoice' in lines[i + 1]:
                audio = match_audio(lines[i + 1])[0]

                if i + 2 < len(lines)and 'Mes(' in lines[i + 2]:
                    text = match_text(lines[i + 2])[0]
                    text = text.replace('「', '').replace('」', '').replace('『', '').replace('』', '').replace('\\n', '')

                    if i + 3 < len(lines) and 'MesWait()' in lines[i + 3]:
                        results.append({'speaker': speaker, 'audio': audio, 'text': text})

    subdir_path = file_path.split('\\')[-2]

    for item in results:
        if debug_mode:
            debug_text = os.path.join(output_dir, f"debug.txt")
            with open(debug_text, 'a', encoding='utf-8') as f:
                f.write(f"{item['audio']}|{item['speaker']}|{item['text']}\n")
        else:
            text_dir = os.path.join(output_dir, item['speaker'])
            text_path = os.path.join(output_dir, item['speaker'], f"{item['audio']}.txt")
            os.makedirs(text_dir, exist_ok=True)
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(item['text'])

if __name__ == '__main__':
    input_dir = r"E:\Dataset\FuckGalGame\#Single\DATE A LIVE - Rio Reincarnation\script"
    output_dir = r"E:\Dataset\FuckGalGame\#Single\DATE A LIVE - Rio Reincarnation\lab"
    debug_mode = False
    
    file_paths = glob(f"{input_dir}/**/*.txt", recursive=True)
    os.makedirs(output_dir, exist_ok=True)

    for file_path in file_paths:
        main(file_path, output_dir, debug_mode=debug_mode)