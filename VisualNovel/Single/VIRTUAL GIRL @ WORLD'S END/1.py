from pathlib import Path

root = Path(r"C:\Users\OOPPEENN\Downloads\VIRTUAL GIRL\Virtual Girl_Data\StreamingAssets\AssetBundles\win")
script_dir = Path(__file__).resolve().parent
output_file = script_dir / "assetbundles_list.txt"

with output_file.open("w", encoding="utf-8") as out_f:
    for file in root.rglob("*"):
        if file.is_file():
            out_f.write(file.relative_to(root).as_posix() + "\n")