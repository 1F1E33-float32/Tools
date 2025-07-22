import argparse
import shutil
from pathlib import Path

def move_paired_files(src_dir: Path, dest_dir: Path):
    acb_map = {f.stem: f for f in src_dir.glob('*.acb')}
    awb_map = {f.stem: f for f in src_dir.glob('*.awb')}

    paired_names = set(acb_map.keys()) & set(awb_map.keys())
    if not paired_names:
        print("未找到任何成对的 .acb 和 .awb 文件。")
        returnw

    dest_dir.mkdir(parents=True, exist_ok=True)

    for name in paired_names:
        for file_path in (acb_map[name], awb_map[name]):
            target = dest_dir / file_path.name
            print(f"{file_path.name} -> {target}")
            shutil.move(str(file_path), str(target))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_folder', default=Path(r"D:\Dataset_Game\com.bandainamcoent.idolmaster_gakuen\RAW\m_audio"))
    parser.add_argument('--output_folder', default=Path(r"D:\Dataset_Game\com.bandainamcoent.idolmaster_gakuen\RAW\m_audio_paired"))
    args = parser.parse_args()

    src = args.input_folder

    dest = args.output_folder
    move_paired_files(src, dest)