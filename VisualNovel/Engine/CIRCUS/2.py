import os
import glob
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor

def convert_files_chunk(chunk, voice_dir, output_dir, mode):
    for pcm_path in chunk:
        relative_path = os.path.relpath(pcm_path, voice_dir)

        if mode == "vgm":
            output_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + ".wav")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            cmd = [r"src\CRICUS\vgmstream-win64\vgmstream-cli.exe", "-o", output_path, pcm_path]
            result = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                print(f"Error converting {pcm_path}:\n{result.stderr}")

        elif mode == "ogg":
            output_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + ".ogg")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(pcm_path, "rb") as f_in:  
                data = f_in.read()
            index = data.find(b"OggS")
            if index != -1:
                ogg_data = data[index:]
                with open(output_path, "wb") as f_out:
                    f_out.write(ogg_data)
            else:
                print(f"No OggS signature found in {pcm_path}. Skipping.")

def convert_pcm_to_wav(voice_dir, output_dir, max_workers=4, mode="vgm"):
    pcm_files = glob.glob(os.path.join(voice_dir, "**", "*.PCM"), recursive=True)
    if not pcm_files:
        print("No .PCM files found. Exiting.")
        return

    chunk_size = math.ceil(len(pcm_files) / max_workers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(0, len(pcm_files), chunk_size):
            chunk = pcm_files[i : i + chunk_size]
            future = executor.submit(convert_files_chunk, chunk, voice_dir, output_dir, mode)
            futures.append(future)

        for future in futures:
            future.result()

if __name__ == "__main__":
    voice_directory = r"D:\Fuck_galgame\pcm"
    output_directory = r"D:\Fuck_galgame\VOICE"
    thread_count = 20

    chosen_mode = "ogg"

    convert_pcm_to_wav(voice_directory, output_directory, max_workers=thread_count, mode=chosen_mode)