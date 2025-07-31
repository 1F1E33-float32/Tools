import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default=r"E:\Game_Dataset\com.aniplex.fategrandorder\RAW\Audio")
    parser.add_argument("--output", type=str, default=r"E:\Game_Dataset\com.aniplex.fategrandorder\EXP\Audio_ENC")
    args = parser.parse_args()

    root = Path(args.root)
    output = Path(args.output)

    output.mkdir(parents=True, exist_ok=True)

    for cpk_file in root.rglob("*.cpk.bytes"):
        print(f"Extracting: {cpk_file}")
        try:
            subprocess.run(["Unity\Fate Grand Order\YACpkTool.exe", str(cpk_file), str(output)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting {cpk_file}: {e}")

if __name__ == "__main__":
    main()