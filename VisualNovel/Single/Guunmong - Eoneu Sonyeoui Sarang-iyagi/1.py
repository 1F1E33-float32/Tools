import os
import csv
import json

BASE_DIR = r"D:\GAL\#KR\Guunmong - Eoneu Sonyeoui Sarang-iyagi\EX"
SUBFOLDERS = ["data", "data_n"]

def parse_csv_file(filepath, results):
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            voice = row.get('c60_Voice')
            if voice and voice.lower() != 'none':
                speaker = row.get('s20_NPCname', '').strip()
                speaker = speaker.replace('?', '？')
                text = row.get('s256_Message', '').strip()
                if '{player name}' in text:
                    continue
                results.append({
                    'Speaker': speaker,
                    'Voice': voice,
                    'Text': text
                })

def main():
    results = []

    for sub in SUBFOLDERS:
        folder = os.path.join(BASE_DIR, sub)
        if not os.path.isdir(folder):
            print(f"Warning: '{folder}' does not exist or is not a directory.")
            continue
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath) and os.path.splitext(filename)[1] == '':
                try:
                    parse_csv_file(filepath, results)
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")

    seen = set()
    unique_results = []
    for entry in results:
        voice = entry.get('Voice')
        if voice and voice not in seen:
            seen.add(voice)
            unique_results.append(entry)
    results = unique_results

    output_path = r"D:\Fuck_galgame\index.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Wrote {len(results)} unique entries to {output_path}")

if __name__ == "__main__":
    main()