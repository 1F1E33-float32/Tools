import os

def clean_file(path):
    signature = b'OggS'
    data = open(path, 'rb').read()
    idx = data.find(signature)
    if idx <= 0:
        return
    with open(path, 'wb') as f:
        f.write(data[idx:])
    print(f"Cleaned: {path}")

if __name__ == "__main__":
    root_folder = r"D:\Dataset_VN_NoScene\HOOKSOFT_Happy Weekend"
    for root, _, files in os.walk(root_folder):
        for name in files:
            if name.lower().endswith('.ogg'):
                clean_file(os.path.join(root, name))