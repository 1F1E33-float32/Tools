import os
import sys

def process_txt(txt_path, in_root, out_root):
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('::')
            if len(parts) < 5:
                continue
            name, ext, dat_name, start_s, length_s = parts[:5]
            try:
                start = int(start_s)
                length = int(length_s)
            except ValueError:
                print(f"跳过非法偏移行：{line}")
                continue

            dat_path = os.path.join(in_root, dat_name)
            if not os.path.isfile(dat_path):
                print(f"找不到 dat 文件：{dat_path}")
                continue

            # 读取并切片
            with open(dat_path, 'rb') as dat_f:
                dat_f.seek(start)
                chunk = dat_f.read(length)

            # 构造输出路径
            subdir = os.path.join(out_root, dat_name)
            os.makedirs(subdir, exist_ok=True)
            out_file = os.path.join(subdir, f"{name}.{ext}")

            # 写入
            with open(out_file, 'wb') as out_f:
                out_f.write(chunk)
            print(f"写出：{out_file}")

def main():
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <输入目录> <输出目录>")
        sys.exit(1)

    in_root = sys.argv[1]
    out_root = sys.argv[2]

    for root, dirs, files in os.walk(in_root):
        for fn in files:
            if fn.lower().endswith('.txt'):
                txt_path = os.path.join(root, fn)
                print(f"处理 {txt_path}")
                process_txt(txt_path, in_root, out_root)

if __name__ == "__main__":
    main()