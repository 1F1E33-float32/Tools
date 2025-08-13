import struct
from pathlib import Path
import lzss
import threading
import collections
import argparse

class FileWrapper:
    def __init__(self, filename, mode="rb"):
        self.file = open(filename, mode)

    def __del__(self):
        self.file.close()

    def seek(self, offset, mode=0):
        self.file.seek(offset, mode)

    def read(self, offset, size):
        self.seek(offset)
        return self.file.read(size)


def extract_S5IN(fd):
    pos = 0x200

    open_archives = {}

    # TODO: Find archive count, trial only has a single arc
    arc_count = 1
    for i in range(arc_count):
        arc_name = fd[pos:fd.find(b"\x00\x00\x00", pos) + 1].decode("utf16")
        pos += 0x200
        arc_entry_count = struct.unpack_from("<I", fd, pos)[0]
        pos += 0x4

        if arc_name not in open_archives:
            open_archives[arc_name] = {"path":Path(arc_name.split(".",1)[0]), "file":FileWrapper(arc_name)}

        print(f"Extracting {hex(arc_entry_count)} entries")
        for x in range(arc_entry_count):
            file_name_len = fd.find(b"\x00\x00", pos)
            file_name_len += file_name_len % 2
            file_name_len -= pos

            file_name = fd[pos:pos + file_name_len].decode("utf16")
            file_offset, file_length = struct.unpack_from("<II", fd, pos + 0x88)
            pos += 0x90

            out_path = open_archives[arc_name]["path"] / file_name
            if not open_archives[arc_name]["path"].exists():
                out_path.mkdir(parents=True, exist_ok=True)

            print(f"offset {hex(file_offset):08X} size {hex(file_length):08X} name {out_path}")

            with open(out_path, "wb") as f:
                f.write(open_archives[arc_name]["file"].read(file_offset, file_length))


def extract_S5IC(fd, is_append, file_filter=""):
    def extract_file(queue_index):
        if len(queues[queue_index]) == 0:
            return

        arc_path = open_archives[queue_index]["path"]
        arc_handle = open_archives[queue_index]["file"]

        out_arc_path = Path("data") / arc_path.stem
        if not out_arc_path.exists():
            out_arc_path.mkdir(parents=True, exist_ok=True)

        while len(queues[queue_index]) > 0:
            entry = queues[queue_index].pop()
            
            file_path = out_arc_path / entry["file_name"]
            print(f"\t{file_path}")

            file_data = arc_handle.read(entry["offset"], entry["length"])
            file_path.write_bytes(file_data)


    pos = 0x214 if is_append else 0x21C

    uncomp_size, uncomp_size2, comp_size = struct.unpack_from("<III", fd, pos)
    fd = fd[pos + 0xC:pos + 0xC + comp_size]
    fd = lzss.decompress(fd, initial_buffer_values=0x0)

    pos = 0

    arc_count = struct.unpack_from("<I", fd, pos)[0]
    pos += 4

    open_archives = {}
    queues = []
    for i in range(arc_count):
        name = fd[pos:fd.find(b"\x00\x00", pos) + 1].decode("utf16").strip()
        open_archives[i] = {"path":Path.cwd() / name, "file":FileWrapper(name)}

        queues.append(collections.deque())

        pos += 0x200

    entry_count = struct.unpack_from("<I", fd, pos)[0]
    pos += 4

    for i in range(entry_count):
        file_name = fd[pos:fd.find(b"\x00\x00", pos) + 1].decode("utf16").strip()

        if file_filter and file_filter.lower() not in file_name.lower():
            pos += 0x90
            continue

        archive_index, file_index, offset, length = struct.unpack_from("<4I", fd, pos + 0x80)
        pos += 0x90

        queues[archive_index].append({"file_name":file_name, "archive_index":archive_index, "file_index":file_index, "offset":offset, "length":length})

    threads = []
    for i in range(arc_count):
        t = threading.Thread(target=extract_file, args=(i,), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


###########################################################################

argp = argparse.ArgumentParser()
argp.add_argument("archive_name", help="Must be \"SYS5INI.BIN\" or \"APPENDxx.AAI\"")
argp.add_argument("-f", "--filter", default="", help="Filter extracted files to ones matching this string, e.g. \".bin\" to get only the script files. Not case sensitive.")

args = argp.parse_args()

if not Path("SYS5INI.BIN").exists():
    print(f"""Could not find \"SYS5INI.BIN\" in this folder. This script expects to be in the game's root folder.""")

with open(args.archive_name, "rb") as f:
    fd = f.read()

magic = fd[:0x8].decode("utf16")
title = fd[0x10:0x110].decode("utf16")

if magic[:3] != "S5I" and magic[:3] != "S5A":
    print(f"SYS5INI.BIN has a bad header, expected S5IN or S5IC, but got {magic}")
    exit()

is_compressed = magic[3] == "C"

print(f"Extracting {title}")

if is_compressed:
    extract_S5IC(fd, magic[2] == "A", args.filter)
else:
    extract_S5IN(fd)