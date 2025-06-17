import subprocess
import sys
from pathlib import Path

# ---- new: locate main.exe next to this script ----
SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_EXE   = SCRIPT_DIR / "epk_tool.exe"

def process_epk(root_dir: Path, mode: str, out_dir: Path):
    if mode not in ('dec', 'enc'):
        raise ValueError("mode must be 'dec' or 'enc'")

    out_dir.mkdir(parents=True, exist_ok=True)

    # choose extension to search
    pattern = '*.epk' if mode == 'dec' else '*.txt'
    for epk_path in root_dir.rglob(pattern):
        rel = epk_path.relative_to(root_dir)
        if mode == 'dec':
            out_path = (out_dir / rel).with_suffix('.txt')
        else:
            out_path = (out_dir / rel).with_suffix('.epk')
        out_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(MAIN_EXE),
            mode,
            str(epk_path),
            str(out_path)
        ]
        print(f"Running: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(res.stdout)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] failed to process {epk_path}:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <dec|enc> <scan_dir> <out_dir>")
        sys.exit(1)

    mode     = sys.argv[1]
    scan_dir = Path(sys.argv[2])
    out_dir  = Path(sys.argv[3])

    process_epk(scan_dir, mode, out_dir)