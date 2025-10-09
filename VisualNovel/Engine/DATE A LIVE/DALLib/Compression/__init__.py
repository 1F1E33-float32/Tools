from io import BytesIO
from typing import Tuple

from ..IO import ExtendedBinaryReader, ExtendedBinaryWriter

LZ77_MAX_WINDOW_SIZE = 0xFF


def compress_lz77(data: bytes) -> bytes:
    memory_stream = BytesIO()
    data_memory_stream = BytesIO()
    writer = ExtendedBinaryWriter(memory_stream)
    data_writer = ExtendedBinaryWriter(data_memory_stream)

    # Write header
    writer.write_signature("LZ77")
    writer.write_int32(len(data))
    # This field is unknown and required by the games
    writer.add_offset("Unknown")
    writer.add_offset("Offset")

    data_pointer = 0
    flag_position = 0
    current_flag = 0

    while data_pointer < len(data):
        best_offset, best_length = find_longest_match(data, data_pointer, 0xFF)

        if best_offset < 0 or best_length < 3:
            # No match
            data_writer.write_byte(data[data_pointer])
            data_pointer += 1
        else:
            # Write match
            current_flag |= 1 << (7 - flag_position)
            data_writer.write_byte(best_offset)  # Back step
            data_writer.write_byte(best_length - 3)  # Amount
            data_pointer += best_length

        flag_position += 1
        if flag_position == 8:
            writer.write_byte(current_flag)
            current_flag = 0
            flag_position = 0

    # Write remaining flags if any
    if flag_position > 0:
        writer.write_byte(current_flag)

    writer.fill_in_offset("Offset")
    writer.write_bytes(data_memory_stream.getvalue())
    writer.fill_in_offset("Unknown")

    return memory_stream.getvalue()


def decompress_lz77(compressed: bytes) -> bytes:
    reader = ExtendedBinaryReader(BytesIO(compressed))

    position = 0
    flag_position = 0
    buffer = None

    # Read header if present
    if reader.read_signature() == "LZ77":
        uncompressed_size = reader.read_int32()
        _ = reader.read_int32()
        offset = reader.read_int32()
        flag_position = reader.get_position()
        reader.jump_to(offset)
        buffer = bytearray(uncompressed_size)
    else:
        raise ValueError("Invalid LZ77 signature")

    flag_count = 0
    flag = 0

    while True:
        if flag_count == 0:
            if flag_position >= len(compressed):
                break
            if flag_position == reader.get_position():
                reader.jump_ahead(1)
            flag = compressed[flag_position]
            flag_position += 1
            flag_count = 8

        if (flag & 0x80) != 0:
            if reader.get_position() + 2 > len(compressed):
                break
            back_step = reader.read_byte()
            amount = reader.read_byte()
            amount += 3

            while amount > 0:
                if position >= len(buffer):
                    break
                buffer[position] = buffer[position - back_step]
                position += 1
                amount -= 1
        else:
            if position >= len(buffer):
                break
            buffer[position] = reader.read_byte()
            position += 1

        flag <<= 1
        flag &= 0xFF  # Keep it as a byte
        flag_count -= 1

    return bytes(buffer)


def find_longest_match(data: bytes, position: int, limit: int) -> Tuple[int, int]:
    window_start = max(position - LZ77_MAX_WINDOW_SIZE, 0)
    max_match_length = min(limit, len(data) - position)

    best_offset = -1
    best_length = -1

    for search_pos in range(window_start, position):
        if data[search_pos] != data[position]:
            continue

        match_length = 1

        while match_length < max_match_length and search_pos + match_length < len(data) and position + match_length < len(data) and data[search_pos + match_length] == data[position + match_length]:
            match_length += 1

        if match_length > best_length:
            best_length = match_length
            best_offset = position - search_pos

            if best_length == max_match_length:
                return best_offset, best_length

    return best_offset, best_length


__all__ = ["compress_lz77", "decompress_lz77", "find_longest_match", "LZ77_MAX_WINDOW_SIZE"]
