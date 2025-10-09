import zlib
from io import BytesIO
from typing import BinaryIO


class StreamTools:
    BLOCKSIZE = 32

    @staticmethod
    def cache_stream(stream: BinaryIO) -> BytesIO:
        memory_stream = BytesIO()
        while True:
            buf = stream.read(StreamTools.BLOCKSIZE)
            if not buf:
                break
            memory_stream.write(buf)
        # Reset position
        memory_stream.seek(0)
        return memory_stream

    @staticmethod
    def deflate_compress(input_stream: BinaryIO, output_stream: BinaryIO) -> int:
        # Store current position of the output stream
        current_position = output_stream.tell()

        # Reset the input stream so we can start reading from it
        input_stream.seek(0)

        # Read all data from input stream
        data = input_stream.read()

        # Compress the data using zlib (deflate)
        compressed_data = zlib.compress(data, level=9)[2:-4]  # Remove zlib header and checksum

        # Write compressed data to output stream
        output_stream.write(compressed_data)

        # Return the size of the compressed data
        return output_stream.tell() - current_position
