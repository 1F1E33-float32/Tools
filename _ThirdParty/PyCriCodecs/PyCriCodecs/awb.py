import os
from io import BytesIO, FileIO
from struct import iter_unpack

from tqdm import tqdm

from .chunk import AWBChunkHeader, HCAType
from tools_boost import hca_decryptor


class AWB:
    def __init__(self, stream, mainkey):
        if isinstance(stream, str):
            self.stream = FileIO(stream)
        else:
            self.stream = BytesIO(stream)

        self.mainkey = mainkey
        self.readheader()

    def readheader(self):
        # Reads header.
        magic, self.version, offset_intsize, self.id_intsize, self.numfiles, self.align, self.subkey = AWBChunkHeader.unpack(self.stream.read(AWBChunkHeader.size))
        if magic != b"AFS2":
            raise ValueError("Invalid AWB header.")

        # Reads data in the header.
        self.ids = list()
        self.ofs = list()
        for i in iter_unpack(f"<{self.stringtypes(self.id_intsize)}", self.stream.read(self.id_intsize * self.numfiles)):
            self.ids.append(i[0])
        for i in iter_unpack(f"<{self.stringtypes(offset_intsize)}", self.stream.read(offset_intsize * (self.numfiles + 1))):
            self.ofs.append(i[0] if i[0] % self.align == 0 else (i[0] + (self.align - (i[0] % self.align))))

        # Seeks to files offset.
        self.headersize = 16 + (offset_intsize * (self.numfiles + 1)) + (self.id_intsize * self.numfiles)
        if self.headersize % self.align != 0:
            self.headersize = self.headersize + (self.align - (self.headersize % self.align))
        self.stream.seek(self.headersize, 0)

    def extract(self, a: dict, exp_dir: str):
        os.makedirs(exp_dir, exist_ok=True)

        rev = {}
        for name, idx_list in a.items():
            if len(idx_list) == 0:
                continue
            if len(idx_list) == 1:
                idx = idx_list[0]
                if idx in rev:
                    rev[idx] = rev[idx] + ";" + name
                else:
                    rev[idx] = name
            else:
                for copy_num, idx in enumerate(idx_list, start=1):
                    new_name = f"{name}_#{copy_num}"
                    if idx in rev:
                        rev[idx] = rev[idx] + ";" + new_name
                    else:
                        rev[idx] = new_name

        segment_count = len(self.ofs) - 1
        if len(rev) != segment_count:
            raise ValueError(f"映射段数 {len(rev)} 与实际段数 {segment_count} 不一致")

        for i in range(1, len(self.ofs)):
            if self.ofs[i] <= self.ofs[i - 1]:
                raise ValueError(f"ofs 非严格递增：ofs[{i - 1}]={self.ofs[i - 1]} >= ofs[{i}]={self.ofs[i]}")

        for i in tqdm(range(segment_count), ncols=150, position=1, leave=False):
            if i not in rev:
                continue

            start = self.ofs[i]
            end = self.ofs[i + 1]
            size = end - start

            self.stream.seek(start, 0)
            data = self.stream.read(size)

            if data.startswith(HCAType.HCA.value):
                pass

            elif data.startswith(HCAType.EHCA.value):
                data = hca_decryptor.decrypt(data, self.mainkey, self.subkey)

            filename = os.path.join(exp_dir, f"{rev[i]}.hca")
            with open(filename, "wb") as f:
                f.write(data)

    def stringtypes(self, intsize: int) -> str:
        if intsize == 1:
            return "B"  # Probably impossible.
        elif intsize == 2:
            return "H"
        elif intsize == 4:
            return "I"
        elif intsize == 8:
            return "Q"
        else:
            raise ValueError("Unknown int size.")
