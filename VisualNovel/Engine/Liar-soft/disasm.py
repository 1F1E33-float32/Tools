import argparse
import struct
import sys
from pathlib import Path
from typing import List


class GscFile:
    CommandsLibrary = (
        (0x03, "i", "JUMP_UNLESS"),
        (0x05, "i", "JUMP"),
        (0x0D, "i", "PAUSE"),
        (0x0C, "ii", "CALL_SCRIPT"),  # [script name without leading zeros, ???]
        (0x0E, "hiiiiiiiiiiiiii", "CHOICE"),
        (0x14, "ii", "IMAGE_GET"),
        (0x1A, "", "IMAGE_SET"),
        (0x1C, "iii", "BLEND_IMG"),
        (0x1E, "iiiiii", "IMAGE_DEF"),
        (0x51, "iiiiiii", "MESSAGE"),
        (0x52, "iiiiii", "APPEND_MESSAGE"),
        (0x53, "i", "CLEAR_MESSAGE_WINDOW"),
        (0x79, "ii", "GET_DIRECTORY"),
        (0xC8, "iiiiiiiiiii", "READ_SCENARIO"),  # ??? adjust arg count if needed
        (0xFF, "iiiii", "SPRITE"),
        (0x3500, "hhh", "AND"),
        (0x4800, "hhh", "EQUALS"),
        (0x5400, "hhh", "GREATER_EQUALS"),
        (0xAA00, "hhh", "ADD"),
        (0xF100, "hh", "ASSIGN"),
        (0x04, "i", ""),
        (0x08, "", ""),
        (0x09, "h", ""),
        (0x0A, "", ""),  # WAIT_FOR_CLICK?
        (0x0B, "", ""),
        (0x0F, "iiiiiiiiiiii", ""),  # ??? array? arg count might need adjustment
        (0x10, "i", ""),
        (0x11, "", ""),
        (0x12, "ii", ""),
        (0x13, "i", ""),
        (0x15, "i", ""),
        (0x16, "iiii", ""),
        (0x17, "iiii", ""),
        (0x18, "ii", ""),
        (0x19, "ii", ""),
        (0x1B, "", ""),
        (0x1D, "ii", ""),
        (0x20, "iiiiii", ""),
        (0x21, "iiiii", ""),
        (0x22, "iiiii", ""),
        (0x23, "ii", ""),
        (0x24, "ii", ""),
        (0x25, "ii", ""),
        (0x26, "iii", ""),  # "Princess of Corruption": iii, others: iiii?
        (0x27, "iii", ""),
        (0x28, "ii", ""),
        (0x29, "ii", ""),
        (0x2A, "ii", ""),
        (0x2B, "ii", ""),
        (0x2C, "i", ""),
        (0x2D, "ii", ""),
        (0x2E, "i", ""),
        (0x2F, "ii", ""),
        (0x30, "ii", ""),  # sometimes ii, others iii?
        (0x31, "ii", ""),
        (0x32, "", ""),
        (0x33, "", ""),
        (0x34, "", ""),
        (0x35, "i", ""),
        (0x37, "", ""),
        (0x38, "iiiii", ""),
        (0x39, "", ""),
        (0x3A, "", ""),
        (0x3B, "iiii", ""),
        (0x3C, "iii", ""),
        (0x3D, "ii", ""),
        (0x3E, "i", ""),  # D&D doc says 'ii'
        (0x3F, "iii", ""),  # D&D doc says 'iiii'
        (0x40, "i", ""),  # D&D doc says 'ii'
        (0x41, "i", ""),
        (0x42, "iiii", ""),
        (0x43, "i", ""),
        (0x44, "", ""),
        (0x45, "", ""),
        (0x46, "iiii", ""),
        (0x47, "iiii", ""),
        (0x48, "i", ""),
        (0x49, "iii", ""),
        (0x4A, "i", ""),
        (0x4B, "iiiii", ""),
        (0x4D, "iiii", ""),
        (0x50, "i", ""),
        (0x5A, "iii", ""),
        (0x5B, "iiiii", ""),
        (0x5C, "ii", ""),
        (0x5D, "ii", ""),
        (0x5E, "i", ""),
        (0x5F, "ii", ""),
        (0x60, "ii", ""),
        (0x61, "ii", ""),
        (0x62, "ii", ""),
        (0x63, "iii", ""),
        (0x64, "iii", ""),
        (0x65, "ii", ""),
        (0x66, "i", ""),
        (0x67, "ii", ""),
        (0x68, "iiii", ""),
        (0x69, "i", ""),  # others ii?
        (0x6A, "iiiii", ""),  # TEMP
        (0x6B, "iii", ""),  # TEMP
        (0x6C, "iii", ""),  # TEMP
        (0x6E, "iii", ""),
        (0x6F, "iii", ""),
        (0x70, "i", ""),
        (0x71, "ii", ""),
        (0x72, "ii", ""),
        (0x73, "ii", ""),
        (0x74, "ii", ""),
        (0x75, "ii", ""),
        (0x78, "ii", ""),
        (0x82, "iiii", ""),
        (0x83, "iiiii", ""),
        (0x84, "ii", ""),
        (0x86, "iii", ""),
        (0x87, "iiiii", ""),
        (0x88, "iii", ""),
        (0x96, "ii", ""),
        (0x97, "ii", ""),
        (0x98, "ii", ""),
        (0x99, "ii", ""),
        (0x9A, "ii", ""),
        (0x9B, "ii", ""),
        (0x9E, "ii", ""),
        (0x9F, "ii", ""),
        (0x9C, "iii", ""),
        (0x9D, "iiiii", ""),
        (0xC9, "iiiii", ""),
        (0xCA, "iii", ""),
        (0xD2, "ii", ""),
        (0xD3, "iiii", ""),
        (0xD4, "i", ""),
        (0xD5, "iii", ""),
        (0xDC, "iii", ""),
        (0xDD, "ii", ""),
        (0xDE, "", ""),
        (0xDF, "ii", ""),
        (0xE1, "iiiii", ""),
        (0xE6, "i", ""),
        (0xE7, "i", ""),
        (0x1800, "hhh", ""),
        (0x1810, "hhh", ""),  # !!!
        (0x1900, "hhh", ""),
        (0x1910, "hhh", ""),
        (0x2500, "hhh", ""),
        (0x1A01, "hhh", ""),  # !!!
        (0x1A00, "hhh", ""),
        (0x4400, "hhh", ""),
        (0x4810, "hhh", ""),  # !!!
        (0x4900, "hhh", ""),
        (0x4A00, "hhh", ""),
        (0x5800, "hhh", ""),
        (0x6800, "hhh", ""),
        (0x7800, "hhh", ""),
        (0x7A00, "hhh", ""),
        (0x8800, "hhh", ""),
        (0x8A00, "hhh", ""),
        (0x9800, "hhh", ""),
        (0x9810, "hhh", ""),  # !!!
        (0x9A00, "hhh", ""),
        (0xA100, "hhh", ""),
        (0xA200, "hhh", ""),
        (0xA201, "hhh", ""),  # !!
        (0xA400, "hhh", ""),
        (0xA500, "hhh", ""),
        (0xA600, "hhh", ""),
        (0xA800, "hhh", ""),
        (0xA810, "hhh", ""),  # !!!
        (0xA900, "hhh", ""),
        (0xB400, "hhh", ""),
        (0xB800, "hhh", ""),
        (0xB900, "hhh", ""),
        (0xC400, "hhh", ""),
        (0xC800, "hhh", ""),
        (0xD400, "hhh", ""),
        (0xD800, "hhh", ""),
        (0xE400, "hhh", ""),
        (0xE800, "hhh", ""),
    )

    ConnectedStringsLibrary = [
        [0x0E, [1, 7, 8, 9, 10, 11]],  # consider removing index 1 if incorrect
        [0x0F, [1]],
        [0x20, [0]],
        [0x51, [-3, -2]],
        [0x52, [-2]],
        [0x79, [1]],
    ]

    ConnectedOffsetsLibrary = [
        [0x03, [0]],
        [0x05, [0]],
        [0x0E, [2, 3, 4, 5, 6]],
        [0xC8, [0]],
    ]

    def __init__(self, in_path: Path):
        self.in_path: Path = in_path
        self.File = None
        # dynamic state
        self.FileParametrs: List[int] = []
        self.FileStruct: List[bytes] = [b"", b"", b"", b"", b""]
        self.FileStringOffsets: List[int] = []
        self.FileStrings: List[str] = []
        self.CommandArgs: List[List[int]] = []
        self.Commands: List[int] = []
        self.Labels: List[List[int]] = []  # [ [label_index, offset], ... ]

    def _open(self):
        self.File = open(self.in_path, mode="rb")

    def _close(self):
        if self.File:
            self.File.close()
            self.File = None

    def ReadHeader(self):
        self.File.seek(0, 0)
        k1 = struct.unpack("ii", self.File.read(8))
        self.FileParametrs.extend(k1)
        k2 = struct.unpack("iiiiiii", self.File.read(self.FileParametrs[1] - 8))
        self.FileParametrs.extend(k2)
        self.File.seek(0, 0)
        self.FileStruct[0] = self.File.read(self.FileParametrs[1])

    def ReadCommand(self, dump_unknown=False):
        self.File.seek(self.FileParametrs[1], 0)
        reader = 0
        cmd_idx = 0
        while reader < self.FileParametrs[2]:
            reader += 2
            code = struct.unpack("H", self.File.read(2))[0]
            # Find argument struct: exact match or infer by mask.
            arg_struct = None
            known = False
            for entry in self.CommandsLibrary:
                if code == entry[0]:
                    arg_struct = entry[1]
                    known = True
                    break
            if not known:
                # Infer args via mask (original heuristic):
                if (code & 0xF000) == 0xF000:
                    arg_struct = "hh"
                elif (code & 0xF000) == 0x0000:
                    arg_struct = ""
                else:
                    arg_struct = "hhh"
                if dump_unknown:
                    print(f"Unknown opcode 0x{code:04X} inferred as '{arg_struct}'")

            self.CommandArgs.append([])
            # Read arguments according to struct.
            for ch in arg_struct:
                if ch in ("i", "I"):
                    size = 4
                elif ch in ("h", "H"):
                    size = 2
                else:
                    raise RuntimeError(f"Bad arg code '{ch}' for opcode {code:#x}")
                reader += size
                self.CommandArgs[cmd_idx].append(struct.unpack(ch, self.File.read(size))[0])

            self.Commands.append(code)
            cmd_idx += 1

        if reader != self.FileParametrs[2]:
            print(f"Command section read={reader} but header says={self.FileParametrs[2]}")

        self.File.seek(self.FileParametrs[1], 0)
        self.FileStruct[1] = self.File.read(self.FileParametrs[2])

    def ReadStringDec(self):
        offset = self.FileParametrs[1] + self.FileParametrs[2]
        self.File.seek(offset, 0)
        self.FileStringOffsets = [struct.unpack("i", self.File.read(4))[0] for _ in range(self.FileParametrs[3] // 4)]
        self.File.seek(offset, 0)
        self.FileStruct[2] = self.File.read(self.FileParametrs[3])

    def ReadStringDef(self):
        offset = self.FileParametrs[1] + self.FileParametrs[2] + self.FileParametrs[3]
        self.File.seek(offset, 0)
        self.FileStrings = []
        for i in range(len(self.FileStringOffsets)):
            if i == len(self.FileStringOffsets) - 1:
                length = self.FileParametrs[4]
            else:
                length = self.FileStringOffsets[i + 1]
            length -= self.FileStringOffsets[i]
            # Read (len-1) bytes, then skip trailing NUL.
            self.FileStrings.append(self.File.read(length - 1).decode("shift_jis"))
            self.File.read(1)
        self.File.seek(offset, 0)
        self.FileStruct[3] = self.File.read(self.FileParametrs[4])

    def ReadRemaining(self):
        offset = self.FileParametrs[1] + self.FileParametrs[2] + self.FileParametrs[3] + self.FileParametrs[4]
        self.File.seek(offset, 0)
        self.FileStruct[4] = b""
        for i in range(5, len(self.FileParametrs)):
            self.FileStruct[4] += self.File.read(self.FileParametrs[i])

    def ReadAll(self, dump_unknown=False):
        self._open()
        try:
            self.ReadHeader()
            self.ReadCommand(dump_unknown=dump_unknown)
            self.ReadStringDec()
            self.ReadStringDef()
            self.ReadRemaining()
        finally:
            self._close()

    def DecompileToTxt(self, out_path: Path):
        # First pass: resolve label offsets into numeric labels.
        label_number = 0
        self.Labels = []
        for cmd_i, op in enumerate(self.Commands):
            lib_idx = next((j for j, ent in enumerate(self.ConnectedOffsetsLibrary) if ent[0] == op), -1)
            if lib_idx == -1:
                continue
            for arg_idx in self.ConnectedOffsetsLibrary[lib_idx][1]:
                target_offset = self.CommandArgs[cmd_i][arg_idx]
                known = next((lab[0] for lab in self.Labels if lab[1] == target_offset), None)
                if known is None:
                    self.Labels.append([label_number, target_offset])
                    self.CommandArgs[cmd_i][arg_idx] = label_number
                    label_number += 1
                else:
                    self.CommandArgs[cmd_i][arg_idx] = known

        # Emit decompiled text.
        with open(out_path, "w", encoding="shift_jis") as f:
            string_count = 0
            offset = 0

            for cmd_i, op in enumerate(self.Commands):
                # Emit label if current code offset matches.
                for lab in self.Labels:
                    if offset == lab[1]:
                        f.write("label_" + str(lab[0]) + "\n")

                # Decide command name & size.
                entry_idx = next((i for i, e in enumerate(self.CommandsLibrary) if e[0] == op), -1)
                known = entry_idx != -1
                if known and self.CommandsLibrary[entry_idx][2]:
                    cmd_name = self.CommandsLibrary[entry_idx][2]
                else:
                    cmd_name = "OP_" + str(op)

                # Advance offset (2 bytes for opcode + args).
                offset += 2
                if known:
                    for ch in self.CommandsLibrary[entry_idx][1]:
                        offset += 2 if ch in ("h", "H") else 4
                else:
                    # Heuristic as in original.
                    if (op & 0xF000) == 0xF000:
                        offset += 4
                    elif (op & 0xF000) == 0x0000:
                        offset += 0
                    else:
                        offset += 6

                # Handle commands that reference string table entries.
                con_idx = next((k for k, ent in enumerate(self.ConnectedStringsLibrary) if ent[0] == op), -1)
                if con_idx != -1:
                    indices = self.ConnectedStringsLibrary[con_idx][1]
                    args_copy = list(self.CommandArgs[cmd_i])  # temp copy to set -1
                    grabbed: List[str] = []
                    for which in indices:
                        msg_index = args_copy[which]
                        args_copy[which] = -1
                        grabbed.append(self.FileStrings[msg_index].replace("^n", "\n"))
                        # Emit any preceding untouched strings in table order.
                        while string_count < msg_index:
                            f.write(">" + str(string_count) + "\n")
                            f.write(self.FileStrings[string_count].replace("^n", "\n") + "\n")
                            string_count += 1
                        string_count += 1
                    f.write(cmd_name + " " + str(args_copy))
                    for z in grabbed:
                        f.write("\n>-1\n" + z)
                else:
                    f.write(cmd_name + " " + str(self.CommandArgs[cmd_i]))

                if cmd_i != len(self.Commands) - 1:
                    f.write("\n")
                else:
                    # Flush any remaining strings.
                    while string_count < len(self.FileStrings):
                        f.write("\n>" + str(string_count) + "\n")
                        # Original behavior: on the final flush, replace '^' with backslash.
                        f.write(self.FileStrings[string_count].replace("^", "\\"))
                        string_count += 1


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("input_dir", type=Path, help="Input directory containing .gsc files (non-recursive).")
    p.add_argument("--dump-unknown", action="store_true")
    return p


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    input_dir = args.input_dir

    gsc_paths = input_dir.glob("*.gsc")
    if not gsc_paths:
        print("No .gsc files found.")
        return 0

    failures = 0
    for in_path in gsc_paths:
        out_path = in_path.with_suffix(".txt")
        try:
            g = GscFile(in_path)
            g.ReadAll(dump_unknown=args.dump_unknown)
            g.DecompileToTxt(out_path)
            print(f"Decompiled: {in_path} -> {out_path}")
        except Exception as e:
            print(f"Failed to decompile {in_path}: {e}")
            failures += 1

    if failures:
        print(f"Completed with {failures} failure(s).")
        return 2

    print("Completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
