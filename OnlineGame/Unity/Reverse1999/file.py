import os
import json
import shutil
import argparse

def copy_and_build(root_dir, index_path, output_dir):
    # Read the master index
    with open(index_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Supported languages
    languages = ['zh', 'en', 'kr', 'jp']

    for lang in languages:
        lang_root = os.path.join(root_dir, lang)
        lang_output = os.path.join(output_dir, lang)
        os.makedirs(lang_output, exist_ok=True)
        lang_index = []

        for entry in entries:
            speaker = entry['Speaker'][lang]
            voice   = str(entry['Voice'])
            directory = entry['Directory']
            text    = entry['Text'][lang]

            # Construct source and destination paths
            src_file = os.path.join(lang_root, directory, voice + '.wav')
            dst_dir  = os.path.join(lang_output, speaker)
            dst_file = os.path.join(dst_dir, voice + '.wav')

            # Ensure destination directory exists

            # Copy if exists, otherwise skip entry
            if os.path.isfile(src_file):
                os.makedirs(dst_dir, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                # Append to this language's index only if copy succeeded
                lang_index.append({
                    'Speaker': speaker,
                    'Voice': voice + '.wav',
                    'Text': text,
                })
            else:
                print(f"[Warning] Missing audio, skipping entry {voice}: {src_file}")

        # Write per-language index.json
        index_out = os.path.join(lang_output, 'index.json')
        with open(index_out, 'w', encoding='utf-8') as f_out:
            json.dump(lang_index, f_out, ensure_ascii=False, indent=2)
        print(f"Wrote {len(lang_index)} entries to {index_out}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',   default=r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\audios\Android_WAV")
    parser.add_argument('--index',  default=r"D:\Dataset_Game\com.bluepoch.m.en.reverse1999\EXP\index.json")
    parser.add_argument('--output', default=r"D:\Dataset_VN_NoScene\#OK L\1999")
    args = parser.parse_args()
    copy_and_build(args.root, args.index, args.output)
