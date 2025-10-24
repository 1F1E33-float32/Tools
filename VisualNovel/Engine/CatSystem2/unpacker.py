import argparse
import glob
import os
import re
import struct

import pefile
from tools_boost import catsystem2_crypto


def _32(x):
    return 0xFFFFFFFF & x


def get_pass_from_exe(filename):
    pe = pefile.PE(filename)

    code_data = None
    key_data = None

    if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if resource_type.name is not None:
                name = resource_type.name.string.decode("utf-8", errors="ignore")
                if name == "V_CODE":
                    for resource_id in resource_type.directory.entries:
                        for resource_lang in resource_id.directory.entries:
                            data_rva = resource_lang.data.struct.OffsetToData
                            size = resource_lang.data.struct.Size
                            code_data = pe.get_data(data_rva, size)
                            break
                        if code_data:
                            break
                elif name == "KEY_CODE":
                    for resource_id in resource_type.directory.entries:
                        for resource_lang in resource_id.directory.entries:
                            data_rva = resource_lang.data.struct.OffsetToData
                            size = resource_lang.data.struct.Size
                            key_data = pe.get_data(data_rva, size)
                            break
                        if key_data:
                            break

    if code_data is None or len(code_data) < 8:
        return None

    if key_data is not None:
        key_data = bytes(b ^ 0xCD for b in key_data)
    else:
        key_data = b"windmill"

    bf = catsystem2_crypto.Blowfish(key_data)
    decrypted_size = len(code_data) // 8 * 8
    decrypted = bf.decrypt(code_data[:decrypted_size])

    # Find null terminator
    null_pos = decrypted.find(b"\x00")
    if null_pos != -1:
        decrypted = decrypted[:null_pos]

    result = decrypted.decode("cp932")
    return result


class ExtractKIF:
    def __init__(self, fk, sk, output_path):
        if output_path is None:
            raise ValueError("output_path is required")

        k00, k01 = struct.unpack("4sI", fk.read(8))
        if k00 != b"KIF\x00":
            raise Exception("IC Violated 0-0")
        flag_decrypt = False
        fileinfo = []
        for i in range(k01):
            k10, k11, k12 = struct.unpack("64sII", fk.read(72))
            fileinfo.append((k10.decode("utf-8").split("\0")[0], k11, k12))
            if fileinfo[-1][0] == "__key__.dat":
                key0 = self.genseed(sk)
                key1 = struct.pack("I", catsystem2_crypto.MT(k12).genrand())
                bf, flag_decrypt = catsystem2_crypto.Blowfish(key1), True

        pathout = output_path
        if not os.path.exists(pathout):
            os.makedirs(pathout)
        for i in range(k01):
            if fileinfo[i][0] == "__key__.dat":
                continue
            if flag_decrypt:
                k10 = self.decfilename(fileinfo[i][0], catsystem2_crypto.MT(key0 + i).genrand())
                k11, k12 = _32(fileinfo[i][1] + i), fileinfo[i][2]
                k11, k12 = struct.unpack("II", bf.decrypt(struct.pack("II", k11, k12)))
                fileinfo[i] = (k10, k11, k12)
            fk.seek(fileinfo[i][1])
            k20 = fk.read(fileinfo[i][2])
            if flag_decrypt:
                k21 = 0xFFFFFFF8 & fileinfo[i][2]
                k20 = bf.decrypt(k20[:k21]) + k20[k21:]
            fo = open(os.path.join(pathout, fileinfo[i][0]), "wb")
            fo.write(k20)
            fo.close()

    def genseed(self, b):
        seed = 0xFFFFFFFF
        for bi in b:
            seed ^= bi << 24
            for _ in range(8):
                if seed & 0x80000000 != 0:
                    seed = (seed ^ 0x80000000) << 1 ^ 0x04C11DB7
                else:
                    seed <<= 1
            seed ^= 0xFFFFFFFF
        return seed

    def decfilename(self, sp, key):
        sft = ((key >> 24) + (key >> 16) + (key >> 8) + (key & 0xFF)) & 0xFF
        sc = []
        for spi in sp:
            if ord(spi) in range(0x41, 0x5B) or ord(spi) in range(0x61, 0x7B):
                sc.append(chr(((103 - sft % 52 - (ord(spi) - 39) % 58) % 52 + 32) % 58 + 65))
            else:
                sc.append(spi)
            sft += 1
        return "".join(sc)


def find_password_from_directory(game_dir):
    exe_files = glob.glob(os.path.join(game_dir, "*.exe"))

    if not exe_files:
        raise Exception(f"No exe files found in {game_dir}")

    # Sort by file size (largest first)
    exe_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
    print(f"Found {len(exe_files)} exe file(s), trying largest first...")

    for exe_file in exe_files:
        size_mb = os.path.getsize(exe_file) / (1024 * 1024)
        print(f"Trying to extract password from: {os.path.basename(exe_file)} ({size_mb:.1f} MB)")
        extracted_pass = get_pass_from_exe(exe_file)
        if extracted_pass:
            print(f"Found password: {extracted_pass}")
            return extracted_pass

    raise Exception("No password found in any exe file")


def process_int_file(int_file_path, output_dir, password):
    print(f"Processing: {os.path.basename(int_file_path)}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(int_file_path, "rb") as f:
        ExtractKIF(f, password.encode("utf-8") if isinstance(password, str) else password, output_dir)


def find_pcm_files(game_dir):
    pattern = os.path.join(game_dir, "pcm_*.int")
    pcm_files = glob.glob(pattern)

    valid_files = []
    for file_path in pcm_files:
        filename = os.path.basename(file_path)
        match = re.match(r"pcm_([a-zA-Z]+)\.int$", filename)
        if match and match.group(1) != "tag":
            valid_files.append(file_path)

    return valid_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default=r"E:\VN\_tmp\#OK\Suzunone Seven!")
    parser.add_argument("--output_dir", default=r"D:\Fuck_VN")

    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    password = find_password_from_directory(input_dir)

    scene_file = os.path.join(input_dir, "scene.int")
    script_output_dir = os.path.join(output_dir, "script")
    process_int_file(scene_file, script_output_dir, password)

    pcm_files = find_pcm_files(input_dir)
    voice_output_dir = os.path.join(output_dir, "voice")

    for pcm_file in pcm_files:
        process_int_file(pcm_file, voice_output_dir, password)
