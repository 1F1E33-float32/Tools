import os
import re
import json
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', default=r"D:\Fuck_galgame\script")
    parser.add_argument('--output_file', default=r"D:\Fuck_galgame\index.json")
    args = parser.parse_args()
    return args

def text_cleaning(text):
    text = re.sub(r"<.*?>", "", text)
    text = text.replace('　', '')
    text = text.replace('「', '').replace('」', '').replace('（', '').replace('）', '').replace('『', '').replace('』', '')
    return text

def parse_voice_text(script: str):
    voice_cmd = re.compile(r'Voice\s*\(\s*"(?P<voice_id>[^"]+)"\s*\)')
    speaker_line = re.compile(r"^(?P<speaker>[^「]+)「(?P<text>[^」]+)」")

    results = []
    lines = script.splitlines()

    for idx, line in enumerate(lines):
        m_voice = voice_cmd.search(line)
        if m_voice:
            voice_id = m_voice.group('voice_id')
            # Look ahead for the next speaker line
            for j in range(idx + 1, len(lines)):
                m_speaker = speaker_line.match(lines[j].strip())
                if m_speaker:
                    speaker = m_speaker.group('speaker').strip()
                    text = m_speaker.group('text').strip()
                    text = text_cleaning(text)
                    results.append({'Speaker': speaker, 'Voice': voice_id, 'Text': text})
                    break
    return results

def process_directory(input_dir: str):
    all_data = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.txt'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        script = f.read()
                    entries = parse_voice_text(script)
                    all_data.extend(entries)
                except Exception as e:
                    print(f"Error processing {path}: {e}")
    return all_data

if __name__ == '__main__':
    args = parse_args()
    data = process_directory(args.input_dir)
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    # Write results to JSON file
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(data)} lines and wrote to {args.output_file}")
