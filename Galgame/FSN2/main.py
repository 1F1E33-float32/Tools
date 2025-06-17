def parse_dat_file(dat_path):
    records = []
    with dat_path.open(encoding="utf-8") as f:
        next(f)
        next(f)
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("::")
            records.append({
                "id": parts[0],
                "label": parts[1],
                "text": parts[2],
            })
    return records

def parse_all_epk_dec(root_dir):
    combined = {}
    for file_path in root_dir.rglob('*.epk_dec'):
        stem = file_path.stem
        records = parse_dat_file(file_path)
        combined[stem] = records
    return combined