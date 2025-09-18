from typing import Dict, Tuple

from .binary import read_fourcc, u16, u32


def detect_endianness(data: bytes) -> bool:
    return read_fourcc(data, 0) == b"RIFX"


def parse_chunks(data: bytes, be: bool):
    size = len(data)
    if size < 12:
        raise ValueError("File too small to be RIFF/RIFX")

    riff = read_fourcc(data, 0)
    if riff not in (b"RIFF", b"RIFX"):
        raise ValueError("Not a RIFF/RIFX file")

    form = read_fourcc(data, 8)
    if form not in (b"WAVE", b"XWMA"):
        raise ValueError("Not a Wwise WAVE/XWMA file")

    chunks = {}
    pos = 12
    while pos + 8 <= size:
        ck_id = read_fourcc(data, pos)
        ck_sz = u32(data, pos + 4, be)
        payload_off = pos + 8

        if payload_off > size:
            break
        if payload_off + ck_sz > size:
            ck_sz = max(0, size - payload_off)

        chunks[ck_id] = (payload_off, ck_sz)
        pos = payload_off + ck_sz
        if pos & 1:
            pos += 1

    return chunks


def parse_fmt_fields(data: bytes, fmt_off: int, fmt_sz: int, be: bool):
    if fmt_sz < 0x10:
        raise ValueError("fmt chunk too small")
    fields: Dict[str, int] = {}
    fields["format"] = u16(data, fmt_off + 0x00, be)
    fields["channels"] = u16(data, fmt_off + 0x02, be)
    fields["sample_rate"] = u32(data, fmt_off + 0x04, be)
    fields["avg_bitrate"] = u32(data, fmt_off + 0x08, be)
    fields["block_size"] = u16(data, fmt_off + 0x0C, be)
    fields["bits_per_sample"] = u16(data, fmt_off + 0x0E, be)
    extra_size = 0
    if fmt_sz > 0x10 and fields["format"] not in (0x0165, 0x0166):
        extra_size = u16(data, fmt_off + 0x10, be)
    fields["extra_size"] = extra_size

    # channel config
    channel_type = 0
    channel_mask = 0
    if extra_size >= 0x06 and fmt_off + 0x18 <= len(data):
        raw = u32(data, fmt_off + 0x14, be)
        if (raw & 0xFF) == fields["channels"]:
            channel_type = (raw >> 8) & 0x0F
            channel_mask = raw >> 12
        else:
            channel_mask = raw
    fields["channel_type"] = channel_type
    fields["channel_mask"] = channel_mask
    return fields


def compute_payload_range(data: bytes, be: bool, chunks: Dict[bytes, Tuple[int, int]]) -> Tuple[int, int, int]:
    if b"fmt " not in chunks or b"data" not in chunks:
        raise ValueError("Missing fmt or data chunk")

    fmt_off, fmt_sz = chunks[b"fmt "]
    data_off, data_sz = chunks[b"data"]
    file_sz = len(data)

    f = parse_fmt_fields(data, fmt_off, fmt_sz, be)
    fmt_code = f["format"]

    if data_off + data_sz > file_sz:
        data_sz = max(0, file_sz - data_off)

    payload_off = data_off
    payload_sz = data_sz

    if fmt_code == 0x3040:  # OPUS (standard Ogg Opus)
        if b"meta" in chunks:
            meta_off, meta_sz = chunks[b"meta"]
            if meta_off + 0x08 <= file_sz:
                meta_skip = u32(data, meta_off + 0x04, be)
                skip = min(meta_skip, payload_sz)
                payload_off += skip
                payload_sz -= skip
    elif fmt_code == 0x3039:  # OPUSNX (Switch)
        if fmt_sz >= 0x28:
            seek_size = u32(data, fmt_off + 0x24, be)
            skip = min(seek_size, payload_sz)
            payload_off += skip
            payload_sz -= skip
    elif fmt_code == 0xFFFF:  # Wwise Vorbis
        if b"vorb" in chunks:
            vorb_off, vorb_sz = chunks[b"vorb"]
            if vorb_sz in (0x2C, 0x28, 0x34, 0x32):
                data_offsets = 0x18
            elif vorb_sz == 0x2A:
                data_offsets = 0x10
            else:
                data_offsets = None
            if data_offsets is not None and vorb_off + data_offsets + 0x08 <= file_sz:
                audio_offset = u32(data, vorb_off + data_offsets + 0x04, be)
                if audio_offset <= payload_sz:
                    payload_off += audio_offset
                    payload_sz -= audio_offset
        else:
            if f.get("extra_size", 0) >= 0x30 and fmt_off + 0x18 + 0x14 <= file_sz:
                audio_offset = u32(data, fmt_off + 0x18 + 0x14, be)
                if audio_offset <= payload_sz:
                    payload_off += audio_offset
                    payload_sz -= audio_offset
    elif fmt_code == 0xFFFE:
        if data[payload_off : payload_off + 4] == b"OggS":
            payload_sz = max(0, file_sz - payload_off)

    if payload_off < 0 or payload_sz < 0 or payload_off + payload_sz > file_sz:
        payload_sz = max(0, min(payload_sz, file_sz - payload_off))

    return fmt_code, payload_off, payload_sz


# ---- misc helpers ----


def codec_name(fmt_code: int) -> str:
    names = {
        0x0001: "PCM",
        0x0002: "IMA_ADPCM",
        0x0069: "IMA_ADPCM_OLD",
        0x0161: "XWMA_WMAv2",
        0x0162: "XWMA_WMAPro",
        0x0165: "XMA2",
        0x0166: "XMA2_FMT",
        0xAAC0: "AAC",
        0xFFF0: "DSP_ADPCM",
        0xFFFB: "HEVAG",
        0xFFFC: "ATRAC9",
        0xFFFE: "PCMEX",
        0xFFFF: "VORBIS_WWISE",
        0x3039: "OPUSNX",
        0x3040: "OPUS_OGG",
        0x3041: "OPUS_WEM",
        0x8311: "PTADPCM",
    }
    return names.get(fmt_code, f"UNKNOWN_0x{fmt_code:04X}")


def guess_extension(fmt_code: int, data: bytes, payload_off: int) -> str:
    have_ogg = data[payload_off : payload_off + 4] == b"OggS"
    if fmt_code in (0x3040, 0x3039) or have_ogg:
        return ".ogg"
    if fmt_code in (0x0165, 0x0166):
        return ".xma"
    if fmt_code in (0x0161, 0x0162):
        return ".xwma"
    if fmt_code == 0xFFFC:
        return ".at9"
    if fmt_code == 0xFFFB:
        return ".vag"
    if fmt_code == 0xFFF0:
        return ".dsp"
    if fmt_code == 0xAAC0:
        return ".aac"
    if fmt_code == 0x0001:
        return ".pcm"
    if fmt_code in (0x0002, 0x0069, 0x8311):
        return ".adpcm"
    if fmt_code == 0x3041:
        return ".opus"
    return ".bin"


def extract_info(data: bytes) -> Dict[str, object]:
    be = detect_endianness(data)
    chunks = parse_chunks(data, be)
    fmt_code, payload_off, payload_sz = compute_payload_range(data, be, chunks)
    fmt_off, fmt_sz = chunks.get(b"fmt ", (None, None))
    return {
        "be": be,
        "chunks": chunks,
        "fmt_code": fmt_code,
        "fmt_off": fmt_off,
        "fmt_sz": fmt_sz,
        "payload_off": payload_off,
        "payload_sz": payload_sz,
    }
