import argparse
from pathlib import Path

from tqdm import tqdm

from PyCriCodecs.acb import ACB
from PyCriCodecs.awb import AWB


def extract_one(acb_path, out_root, mainkey):
    acb = ACB(str(acb_path))

    embedded_awb_bytes = None
    try:
        payload = getattr(acb, "_payload", None)
        if payload and len(payload) >= 1:
            awb_field = payload[0].get("AwbFile")
            if isinstance(awb_field, (list, tuple)) and len(awb_field) >= 2:
                if isinstance(awb_field[1], (bytes, bytearray)) and len(awb_field[1]) > 0:
                    embedded_awb_bytes = awb_field[1]
    except Exception:
        pass

    if embedded_awb_bytes:
        awb = AWB(embedded_awb_bytes, mainkey)
    else:
        external_awb = acb_path.with_suffix(".awb")
        if not external_awb.exists():
            return
        awb = AWB(str(external_awb), mainkey)

    out_dir = out_root / acb_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    a = acb.extract()
    AWB.extract(awb, a, str(out_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_dir", default=r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\RAW\v")
    parser.add_argument("--out_dir", default=r"D:\Dataset_Game\jp.co.cygames.princessconnectredive\EXP\v")
    parser.add_argument("--mainkey", default=0x000000000030D9E8)
    args = parser.parse_args()

    root = Path(args.in_dir)
    out_root = Path(args.out_dir)
    if not root.exists():
        raise FileNotFoundError(f"输入目录不存在：{root}")

    acb_files = list(root.rglob("*.acb"))

    for acb_path in tqdm(acb_files, ncols=150):
        extract_one(acb_path, out_root, args.mainkey)
