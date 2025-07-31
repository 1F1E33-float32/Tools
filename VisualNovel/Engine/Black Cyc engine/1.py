#!/usr/bin/env python3
import sys
import os
import struct

# 全局参数（示例值，可根据实际情况修改）
DWORD_59BD08 = 0xFFFFFFFF
DWORD_5B5DF4 = 0x00
DWORD_5B5DF8 = 0x00

def process_file(file_path):
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    # 读取文件内容
    with open(file_path, "rb") as f:
        file_data = f.read()

    file_size = len(file_data)
    if file_size % 4 != 0:
        print("文件大小不是4字节的整数倍，可能存在格式问题。")
        return

    # 解析为无符号整数列表，使用 little-endian 格式
    num_integers = file_size // 4
    fmt = f"<{num_integers}I"
    int_list = list(struct.unpack(fmt, file_data))

    # 数据解混淆处理
    v6 = DWORD_59BD08
    v7 = 0
    processed_ints = []
    for value in int_list:
        new_value = (v7 + (v6 ^ value)) & 0xFFFFFFFF  # 保持32位无符号整数
        processed_ints.append(new_value)
        v6 = (v6 + DWORD_5B5DF4) & 0xFFFFFFFF
        v7 = (v7 + DWORD_5B5DF8) & 0xFFFFFFFF

    # 提取头部信息，根据 C 代码中各个偏移位置（单位为字节）
    header = {}
    def get_int_at(offset_bytes):
        index = offset_bytes // 4
        return processed_ints[index] if index < len(processed_ints) else None

    # 假定文件头第 4 个数据（偏移 0）为文件头标识
    header['file_header'] = processed_ints[0] if processed_ints else None
    header['header_16'] = get_int_at(16)  # 对应第5个整数（索引4）
    header['header_20'] = get_int_at(20)  # 索引5
    header['header_24'] = get_int_at(24)  # 索引6
    header['header_28'] = get_int_at(28)  # 索引7
    header['header_40'] = get_int_at(40)  # 索引10
    header['header_72'] = get_int_at(72)  # 索引18

    # 根据文件头中第一个整数判断是否存在额外头部信息
    if processed_ints[0] < 32:
        header['header_80'] = 0
        header['header_84'] = 0
        header['header_88'] = 0
        header['header_92'] = 0
    else:
        header['header_80'] = get_int_at(80)  # 索引20
        header['header_84'] = get_int_at(84)  # 索引21
        header['header_88'] = get_int_at(88)  # 索引22
        header['header_92'] = get_int_at(92)  # 索引23

    # 输出处理后的头部信息
    print("处理后的头部信息：")
    for key, value in header.items():
        if value is not None:
            print(f"{key}: {value:#010x}")
        else:
            print(f"{key}: None")

    # 将处理后的数据写入新文件（保存为 .processed 文件）
    output_path = file_path + ".processed"
    with open(output_path, "wb") as f_out:
        for num in processed_ints:
            f_out.write(struct.pack("<I", num))
    print(f"处理后的数据已写入文件：{output_path}")

def main():
    file_path = r"E:\Games\Galgame\CYCLET\Dasaku\spt\hanami.spt"
    process_file(file_path)

if __name__ == "__main__":
    main()