import os
import subprocess
import threading

print_lock = threading.Lock()

def main(file_path):
    psb_decompile_path = os.path.join(os.path.dirname(__file__), 'PsbDecompile.exe')
    command = [psb_decompile_path, file_path]
    subprocess.run(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def process_files(file_list):
    for file_path in file_list:
        main(file_path)

if __name__ == '__main__':
    input_directory_path = r"D:\GAL\2025_07\Kioku no Kenban\Extractor_Output\data"
    THREAD_NUM = 20

    scn_files = []
    for root, _, files in os.walk(input_directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            scn_files.append(file_path)

    actual_threads = min(THREAD_NUM, len(scn_files))

    chunks = [scn_files[i::actual_threads] for i in range(actual_threads)]
    chunks = [chunk for chunk in chunks if chunk]

    threads = []
    for chunk in chunks:
        thread = threading.Thread(target=process_files, args=(chunk,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()