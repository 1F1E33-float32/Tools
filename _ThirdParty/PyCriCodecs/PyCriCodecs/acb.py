from .chunk import UTFType, UTFTypeValues
from .utf import UTF


class ACB:
    def __init__(self, filename):
        self._payload = UTF(filename).get_payload()
        self.acbparse(self._payload)

    def acbparse(self, payload):
        for dict in range(len(payload)):
            for k, v in payload[dict].items():
                if v[0] == UTFTypeValues.bytes:
                    if v[1].startswith(UTFType.UTF.value):  # or v[1].startswith(UTFType.EUTF.value): # ACB's never gets encrypted?
                        par = UTF(v[1])
                        par = par.get_payload()
                        payload[dict][k] = par
                        self.acbparse(par)

    def extract(self):
        payload = self._payload[0]

        def u8(b, o):
            return b[o]

        def u16be(b, o):
            return int.from_bytes(b[o : o + 2], "big", signed=False)

        def s16be(b, o):
            return int.from_bytes(b[o : o + 2], "big", signed=True)

        wave_table = payload.get("WaveformTable", []) or []
        synth_table = payload.get("SynthTable", []) or []
        seq_table = payload.get("SequenceTable", []) or []
        track_table = payload.get("TrackTable", []) or []
        tevt_table = payload.get("TrackEventTable", []) or []
        cue_table = payload.get("CueTable", []) or []

        # 读取一个 Waveform 索引对应的 AWB id(们)
        def ids_from_waveform_index(idx):
            ids = set()
            if idx < 0 or idx >= len(wave_table):
                return ids
            wf = wave_table[idx]
            # 有些 ACB 直接有 Id 字段；更多情况下看 Streaming 决定取哪个
            streaming = wf.get("Streaming", (None, None))[1]
            # 守护：有时没有 Streaming 字段，尽量猜测
            if streaming is None:
                streaming = 1 if "StreamAwbId" in wf else 0
            # 0=memory, 1=stream, 2=memory(prefetch)+stream
            if streaming in (1, 2):
                sid = wf.get("StreamAwbId", (None, None))[1]
                if sid is not None and sid != 0xFFFF:
                    ids.add(int(sid))
            if streaming in (0, 2):
                mid = wf.get("MemoryAwbId", (None, None))[1]
                if mid is not None and mid != 0xFFFF:
                    ids.add(int(mid))
            # 兜底：有 Id 字段时也收一下
            if "Id" in wf:
                wid = wf["Id"][1]
                if wid is not None and wid != 0xFFFF:
                    ids.add(int(wid))
            return ids

        # 递归：Synth.ReferenceItems = [(type,u16),(index,u16)]*N
        def collect_from_synth(idx, depth=0):
            ids = set()
            if idx < 0 or idx >= len(synth_table) or depth > 3:
                return ids
            ref_bytes = synth_table[idx].get("ReferenceItems", (None, b""))[1] or b""
            # 每 4 字节一项
            for off in range(0, len(ref_bytes), 4):
                if off + 4 > len(ref_bytes):
                    break
                item_type = u16be(ref_bytes, off + 0)
                item_idx = u16be(ref_bytes, off + 2)
                # 0x00: no reference -> 结束
                if item_type == 0x00:
                    break
                elif item_type == 0x01:  # Waveform
                    ids |= ids_from_waveform_index(item_idx)
                elif item_type == 0x02:  # Synth
                    ids |= collect_from_synth(item_idx, depth + 1)
                elif item_type == 0x03:  # Sequence
                    ids |= collect_from_sequence(item_idx, depth + 1)
                else:
                    # 未知类型：按照 C 里做法，停止本 synth 的继续解析
                    break
            return ids

        # 递归：Sequence 里拿 TrackIndex 列表（be s16），逐个 Track → TrackEvent(TLV)
        def collect_from_sequence(idx, depth=0):
            ids = set()
            if idx < 0 or idx >= len(seq_table) or depth > 3:
                return ids
            row = seq_table[idx]
            num_tracks = row.get("NumTracks", (None, 0))[1] or 0
            track_idx_bytes = row.get("TrackIndex", (None, b""))[1] or b""
            # 有时有 padding，这里按 NumTracks 限制
            for i in range(min(num_tracks, len(track_idx_bytes) // 2)):
                t_idx = s16be(track_idx_bytes, i * 2)
                if 0 <= t_idx < len(track_table):
                    ids |= collect_from_track(t_idx, depth + 1)
            return ids

        # Track → EventIndex → TrackEventTable.Command(TLV)
        def collect_from_track(idx, depth=0):
            ids = set()
            if idx < 0 or idx >= len(track_table):
                return ids
            ev_idx = track_table[idx].get("EventIndex", (None, 0xFFFF))[1]
            if ev_idx is None or ev_idx == 0xFFFF:
                return ids
            if ev_idx < 0 or ev_idx >= len(tevt_table):
                return ids
            cmd_bytes = tevt_table[ev_idx].get("Command", (None, b""))[1] or b""
            pos, end = 0, len(cmd_bytes)
            while pos + 3 <= end:
                tlv_code = u16be(cmd_bytes, pos + 0)
                tlv_size = u8(cmd_bytes, pos + 2)
                pos += 3
                # noteOn / noteOnWithNo
                if tlv_code in (2000, 2003):
                    if pos + 4 <= end:
                        tlv_type = u16be(cmd_bytes, pos + 0)
                        tlv_index = u16be(cmd_bytes, pos + 2)
                        if tlv_type == 0x02:  # Synth
                            ids |= collect_from_synth(tlv_index, depth + 1)
                        elif tlv_type == 0x03:  # Sequence
                            ids |= collect_from_sequence(tlv_index, depth + 1)
                        # 其它类型不处理（和 C 一致）
                # 其它 TLV 忽略
                pos += tlv_size
            return ids

        # BlockSequence（少见）：只尽量读取 TrackIndex（Block 忽略）
        def collect_from_blocksequence(idx, depth=0):
            ids = set()
            bq = payload.get("BlockSequenceTable")
            if not isinstance(bq, list):
                return ids
            if idx < 0 or idx >= len(bq):
                return ids
            row = bq[idx]
            num_tracks = row.get("NumTracks", (None, 0))[1] or 0
            track_idx_bytes = row.get("TrackIndex", (None, b""))[1] or b""
            for i in range(min(num_tracks, len(track_idx_bytes) // 2)):
                t_idx = s16be(track_idx_bytes, i * 2)
                if 0 <= t_idx < len(track_table):
                    ids |= collect_from_track(t_idx, depth + 1)
            return ids

        # 先把 CueIndex → CueName 做成映射
        cue_names_index_mapping = {}
        for item in payload.get("CueNameTable", []) or []:
            cue_names_index_mapping[item["CueIndex"][1]] = item["CueName"][1]

        result = {}
        for i, cue_name in cue_names_index_mapping.items():
            if i < 0 or i >= len(cue_table):
                continue
            ref_index = cue_table[i].get("ReferenceIndex", (None, None))[1]
            ref_type = cue_table[i].get("ReferenceType", (None, None))[1]

            wave_ids = set()
            if ref_index is None or ref_type is None:
                result[cue_name] = []
                continue

            if ref_type == 0x01:  # Cue > Waveform
                wave_ids |= ids_from_waveform_index(ref_index)
            elif ref_type == 0x02:  # Cue > Synth > Waveform
                wave_ids |= collect_from_synth(ref_index)
            elif ref_type == 0x03:  # Cue > Sequence > Track > Command > ...
                wave_ids |= collect_from_sequence(ref_index)
            elif ref_type == 0x08:  # Cue > BlockSequence > ...
                wave_ids |= collect_from_blocksequence(ref_index)
            else:
                pass

            result[cue_name] = sorted(wave_ids)

        return result
