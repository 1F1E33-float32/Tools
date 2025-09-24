import os
import shutil


def main():
    src_folder = r"D:\GAL\2025_07\Kioku no Kenban\Extractor_Output\voice"
    dst_folder = r"D:\Fuck_galgame\voice"

    # 如果目标文件夹不存在，则创建
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
        print(f"已创建目标文件夹: {dst_folder}")

    # 1. 递归扫描源文件夹及其子文件夹中所有没有后缀名的文件（名称为 hash 值）
    # 将文件名和完整路径存入字典 listA
    listA = {}
    for root, dirs, files in os.walk(src_folder):
        for file in files:
            file_path = os.path.join(root, file)
            name, ext = os.path.splitext(file)
            if ext == "":
                listA[file] = file_path

    print(f"在源文件夹及子文件夹中共找到 {len(listA)} 个没有后缀名的文件。")

    # 2. 读取 files_match.txt 文件，建立 hash -> 原始文件名 的映射
    mapping = {}  # 键：hash 值；值：对应的原始文件名（包含扩展名）
    try:
        with open(r"D:\Fuck_galgame\files_match.txt", "r", encoding="utf-16-le") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # 每行格式： 文件名,hash值
                parts = line.split(",")
                if len(parts) != 2:
                    print(f"跳过格式不对的行: {line}")
                    continue
                original_filename = parts[0].strip()
                hash_value = parts[1].strip()
                mapping[hash_value] = original_filename
    except FileNotFoundError:
        print("未找到 files_match.txt 文件，请确认文件位置！")
        return

    print(f"从 files_match.txt 中读取到 {len(mapping)} 条匹配信息。")

    # 3. 根据 mapping 遍历每个 hash 值，在 listA 中查找对应的文件，如果存在，则复制并重命名到目标文件夹
    copied_count = 0
    for hash_value, original_filename in mapping.items():
        if hash_value in listA:
            src_file_path = listA[hash_value]
            dst_file_path = os.path.join(dst_folder, original_filename)
            try:
                shutil.copy2(src_file_path, dst_file_path)
                copied_count += 1
            except Exception as e:
                print(f"复制 {hash_value} 时发生错误: {e}")

    print(f"共复制并重命名了 {copied_count} 个文件到目标文件夹：{dst_folder}")


if __name__ == "__main__":
    main()
