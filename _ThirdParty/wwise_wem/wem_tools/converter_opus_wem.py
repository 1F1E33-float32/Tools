import struct
from typing import Dict, List, Tuple

from .binary import le16, le16s, le32
from .extractor import u16, u32


def crc32_ogg(data: bytes) -> int:
    # fmt: off
    table = [
        0x00000000,0x04c11db7,0x09823b6e,0x0d4326d9,0x130476dc,0x17c56b6b,0x1a864db2,0x1e475005,
        0x2608edb8,0x22c9f00f,0x2f8ad6d6,0x2b4bcb61,0x350c9b64,0x31cd86d3,0x3c8ea00a,0x384fbdbd,
        0x4c11db70,0x48d0c6c7,0x4593e01e,0x4152fda9,0x5f15adac,0x5bd4b01b,0x569796c2,0x52568b75,
        0x6a1936c8,0x6ed82b7f,0x639b0da6,0x675a1011,0x791d4014,0x7ddc5da3,0x709f7b7a,0x745e66cd,
        0x9823b6e0,0x9ce2ab57,0x91a18d8e,0x95609039,0x8b27c03c,0x8fe6dd8b,0x82a5fb52,0x8664e6e5,
        0xbe2b5b58,0xbaea46ef,0xb7a96036,0xb3687d81,0xad2f2d84,0xa9ee3033,0xa4ad16ea,0xa06c0b5d,
        0xd4326d90,0xd0f37027,0xddb056fe,0xd9714b49,0xc7361b4c,0xc3f706fb,0xceb42022,0xca753d95,
        0xf23a8028,0xf6fb9d9f,0xfbb8bb46,0xff79a6f1,0xe13ef6f4,0xe5ffeb43,0xe8bccd9a,0xec7dd02d,
        0x34867077,0x30476dc0,0x3d044b19,0x39c556ae,0x278206ab,0x23431b1c,0x2e003dc5,0x2ac12072,
        0x128e9dcf,0x164f8078,0x1b0ca6a1,0x1fcdbb16,0x018aeb13,0x054bf6a4,0x0808d07d,0x0cc9cdca,
        0x7897ab07,0x7c56b6b0,0x71159069,0x75d48dde,0x6b93dddb,0x6f52c06c,0x6211e6b5,0x66d0fb02,
        0x5e9f46bf,0x5a5e5b08,0x571d7dd1,0x53dc6066,0x4d9b3063,0x495a2dd4,0x44190b0d,0x40d816ba,
        0xaca5c697,0xa864db20,0xa527fdf9,0xa1e6e04e,0xbfa1b04b,0xbb60adfc,0xb6238b25,0xb2e29692,
        0x8aad2b2f,0x8e6c3698,0x832f1041,0x87ee0df6,0x99a95df3,0x9d684044,0x902b669d,0x94ea7b2a,
        0xe0b41de7,0xe4750050,0xe9362689,0xedf73b3e,0xf3b06b3b,0xf771768c,0xfa325055,0xfef34de2,
        0xc6bcf05f,0xc27dede8,0xcf3ecb31,0xcbffd686,0xd5b88683,0xd1799b34,0xdc3abded,0xd8fba05a,
        0x690ce0ee,0x6dcdfd59,0x608edb80,0x644fc637,0x7a089632,0x7ec98b85,0x738aad5c,0x774bb0eb,
        0x4f040d56,0x4bc510e1,0x46863638,0x42472b8f,0x5c007b8a,0x58c1663d,0x558240e4,0x51435d53,
        0x251d3b9e,0x21dc2629,0x2c9f00f0,0x285e1d47,0x36194d42,0x32d850f5,0x3f9b762c,0x3b5a6b9b,
        0x0315d626,0x07d4cb91,0x0a97ed48,0x0e56f0ff,0x1011a0fa,0x14d0bd4d,0x19939b94,0x1d528623,
        0xf12f560e,0xf5ee4bb9,0xf8ad6d60,0xfc6c70d7,0xe22b20d2,0xe6ea3d65,0xeba91bbc,0xef68060b,
        0xd727bbb6,0xd3e6a601,0xdea580d8,0xda649d6f,0xc423cd6a,0xc0e2d0dd,0xcda1f604,0xc960ebb3,
        0xbd3e8d7e,0xb9ff90c9,0xb4bcb610,0xb07daba7,0xae3afba2,0xaafbe615,0xa7b8c0cc,0xa379dd7b,
        0x9b3660c6,0x9ff77d71,0x92b45ba8,0x9675461f,0x8832161a,0x8cf30bad,0x81b02d74,0x857130c3,
        0x5d8a9099,0x594b8d2e,0x5408abf7,0x50c9b640,0x4e8ee645,0x4a4ffbf2,0x470cdd2b,0x43cdc09c,
        0x7b827d21,0x7f436096,0x7200464f,0x76c15bf8,0x68860bfd,0x6c47164a,0x61043093,0x65c52d24,
        0x119b4be9,0x155a565e,0x18197087,0x1cd86d30,0x029f3d35,0x065e2082,0x0b1d065b,0x0fdc1bec,
        0x3793a651,0x3352bbe6,0x3e119d3f,0x3ad08088,0x2497d08d,0x2056cd3a,0x2d15ebe3,0x29d4f654,
        0xc5a92679,0xc1683bce,0xcc2b1d17,0xc8ea00a0,0xd6ad50a5,0xd26c4d12,0xdf2f6bcb,0xdbee767c,
        0xe3a1cbc1,0xe760d676,0xea23f0af,0xeee2ed18,0xf0a5bd1d,0xf464a0aa,0xf9278673,0xfde69bc4,
        0x89b8fd09,0x8d79e0be,0x803ac667,0x84fbdbd0,0x9abc8bd5,0x9e7d9662,0x933eb0bb,0x97ffad0c,
        0xafb010b1,0xab710d06,0xa6322bdf,0xa2f33668,0xbcb4666d,0xb8757bda,0xb5365d03,0xb1f740b4,
    ]
    # fmt:on
    crc = 0
    for b in data:
        idx = ((crc >> 24) & 0xFF) ^ b
        crc = ((crc << 8) & 0xFFFFFFFF) ^ table[idx]
    return crc & 0xFFFFFFFF


def _opus_packet_samples_per_frame(toc0: int, Fs: int = 48000) -> int:
    if toc0 & 0x80:
        audiosize = (toc0 >> 3) & 0x3
        audiosize = (Fs << audiosize) // 400
    elif (toc0 & 0x60) == 0x60:
        audiosize = Fs // 50 if (toc0 & 0x08) else Fs // 100
    else:
        audiosize = (toc0 >> 3) & 0x3
        if audiosize == 3:
            audiosize = Fs * 60 // 1000
        else:
            audiosize = (Fs << audiosize) // 100
    return audiosize


def _opus_packet_nb_frames(packet0: int, packet1: int | None = None, length: int = 0) -> int:
    if length < 1:
        return 0
    count = packet0 & 0x3
    if count == 0:
        return 1
    elif count != 3:
        return 2
    else:
        if length < 2 or packet1 is None:
            return 0
        return packet1 & 0x3F


def _build_opus_head(
    channels: int,
    skip: int,
    sample_rate: int,
    stream_count: int,
    coupled_count: int,
    mapping_table: List[int],
    mapping_family: int,
) -> bytes:
    head = bytearray()
    head += b"OpusHead"
    head += bytes([1])
    head += bytes([channels & 0xFF])
    head += le16s(skip)
    head += le32(sample_rate)
    head += le16(0)
    head += bytes([mapping_family])

    if mapping_family in (1, 255):
        head += bytes([stream_count & 0xFF])
        head += bytes([coupled_count & 0xFF])
        use_identity = all(v == 0 for v in mapping_table)
        for i in range(channels):
            head += bytes([(i if use_identity else mapping_table[i]) & 0xFF])
    return bytes(head)


def _lace_for_packet(size: int) -> List[int]:
    laces: List[int] = []
    while size >= 255:
        laces.append(255)
        size -= 255
    laces.append(size)
    return laces


def _build_oggs_page_multi(payload: bytes, laces: List[int], seqno: int, granule: int, bos: bool = False, eos: bool = False, serial: int = 0x7667) -> bytes:
    header = bytearray()
    header += b"OggS"
    header += bytes([0])
    header_type = 0
    if bos:
        header_type |= 0x02
    if eos:
        header_type |= 0x04
    header += bytes([header_type])
    header += le32(granule & 0xFFFFFFFF) + le32((granule >> 32) & 0xFFFFFFFF)
    header += le32(serial)
    header += le32(seqno)
    header += le32(0)
    header += bytes([len(laces)])
    header += bytes(laces)

    page = bytes(header) + payload
    chks = crc32_ogg(page)
    page = page[:22] + le32(chks) + page[26:]
    return page


def _opusww_coupled_count_for_channels(ch: int) -> int:
    mapping = {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3}
    return mapping.get(ch, 0)


def rewrap_opus_wwise_to_ogg(data: bytes, be: bool, chunks: Dict[bytes, Tuple[int, int]], fmt_off: int) -> bytes:
    channels = u16(data, fmt_off + 0x02, be)
    sample_rate = 48000
    table_count = u32(data, fmt_off + 0x1C, be)
    skip = u16(data, fmt_off + 0x20, be)
    version = data[fmt_off + 0x22]
    mapping_val = data[fmt_off + 0x23]

    if version != 1:
        raise ValueError(f"Unsupported OPUS_WEM version: {version}")
    if b"seek" not in chunks or b"data" not in chunks:
        raise ValueError("Missing 'seek' or 'data' chunk for OPUS_WEM")

    seek_off, seek_sz = chunks[b"seek"]
    data_off, data_sz = chunks[b"data"]
    if seek_sz < table_count * 2:
        table_count = seek_sz // 2

    stream_count = 1
    coupled_count = 0
    mapping_table: List[int] = [0] * channels
    mapping_family = 0

    if channels <= 2 and mapping_val == 0:
        mapping_family = 0
        stream_count = 1
        coupled_count = 1 if channels == 2 else 0
    elif mapping_val == 1:
        mapping_family = 1
        if channels > 8:
            mapping_family = 255
            stream_count = channels
            coupled_count = 0
            mapping_table = list(range(channels))
        else:
            coupled_count = _opusww_coupled_count_for_channels(channels)
            stream_count = channels - coupled_count
            mapping_matrix = [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 2, 1, 0, 0, 0, 0, 0],
                [0, 1, 2, 3, 0, 0, 0, 0],
                [0, 4, 1, 2, 3, 0, 0, 0],
                [0, 4, 1, 2, 3, 5, 0, 0],
                [0, 6, 1, 2, 3, 4, 5, 0],
                [0, 6, 1, 2, 3, 4, 5, 7],
            ]
            mapping_table = mapping_matrix[channels - 1][:channels]
    elif mapping_val == 255:
        mapping_family = 255
        stream_count = channels
        coupled_count = 0
        mapping_table = list(range(channels))
    else:
        mapping_family = 1
        coupled_count = _opusww_coupled_count_for_channels(channels)
        stream_count = channels - coupled_count
        mapping_table = list(range(channels))

    head_payload = _build_opus_head(channels, skip, sample_rate, stream_count, coupled_count, mapping_table, mapping_family)
    comment_vendor = b"wem_extract"
    comment_user = b"wem_extract Wwise Opus rewrap"
    comment_payload = bytearray()
    comment_payload += b"OpusTags"
    comment_payload += le32(len(comment_vendor))
    comment_payload += comment_vendor
    comment_payload += le32(1)
    comment_payload += le32(len(comment_user))
    comment_payload += comment_user

    out = bytearray()
    out += _build_oggs_page_multi(head_payload, _lace_for_packet(len(head_payload)), seqno=0, granule=0, bos=True)
    out += _build_oggs_page_multi(bytes(comment_payload), _lace_for_packet(len(comment_payload)), seqno=1, granule=0)

    packets: List[bytes] = []
    phys = data_off
    for i in range(table_count):
        size_i = struct.unpack_from("<H", data, seek_off + i * 2)[0]
        if size_i == 0:
            continue
        if phys + size_i > data_off + data_sz:
            size_i = max(0, (data_off + data_sz) - phys)
        if size_i <= 0:
            break
        packets.append(data[phys : phys + size_i])
        phys += size_i

    seqno = 2
    samples_done = 0
    page_payload = bytearray()
    page_laces: List[int] = []

    def flush_page(eos_flag: bool = False):
        nonlocal out, page_payload, page_laces, seqno, samples_done
        if not page_payload:
            return
        granule = samples_done - skip
        if granule < 0:
            granule = 0
        out += _build_oggs_page_multi(bytes(page_payload), list(page_laces), seqno=seqno, granule=granule, eos=eos_flag)
        seqno += 1
        page_payload.clear()
        page_laces.clear()

    for pkt in packets:
        laces = _lace_for_packet(len(pkt))
        if len(page_laces) + len(laces) > 255:
            flush_page()
        page_payload += pkt
        page_laces.extend(laces)
        toc0 = pkt[0]
        packet1 = pkt[1] if len(pkt) >= 2 else 0
        nb_frames = _opus_packet_nb_frames(toc0, packet1, len(pkt))
        spf = _opus_packet_samples_per_frame(toc0, 48000)
        samples_done += nb_frames * spf

    flush_page(eos_flag=True)
    return bytes(out)
