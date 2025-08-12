import struct
from io import BytesIO
from typing import Optional, List, Tuple

from utils.muxer.dataClasses import Box, TrunSampleEntry


class DashedParser:
    ATOM_TKHD = 0x746B6864  # 'tkhd'
    ATOM_MDIA = 0x6D646961  # 'mdia'
    last_retrieved_sample_index: int = -1

    def __init__(self, file_path: str):
        self.reader = open(file_path, "rb")
        self.current_box = Box()
        self.movie_timescale: int = -1
        self.movie_duration: int = -1

        self.media_timescale: int = -1
        self.media_duration: int = -1
        self.language: str = ""

        self.track_duration: int = -1

        # From hdlr
        self.handler_type: str = ""

        self.stsd_box: Optional[bytes] = None

        self.moofs: List[Box] = []
        self.current_moof_index: int = 0

        self.entries: List[TrunSampleEntry] = []

        self.total_samples_from_moof: int = 0

        # Fields updated from DashedWriter
        self.key_samples_indices: List[int] = []
        self.chunks_offsets: List[int] = []
        self.samples_sizes: List[int] = []
        self.ctts_entries: List[Tuple[int, int]] = []

        self.last_offset: Optional[int] = None
        self.run_length: int = 0
        self.initial_chunk: bool = True
        self.samples_per_chunk_list: List[int] = []

    def parse(self):
        self.reader.seek(0, 0)  # Seek to beginning of file

        def read_int():
            return int.from_bytes(self.reader.read(4), byteorder='big')

        def read_fully(n):
            data = self.reader.read(n)
            if len(data) != n:
                raise EOFError(f"Expected {n} bytes, got {len(data)}")
            return data

        file_length = self.reader.seek(0, 2)  # Seek to end to get file length
        self.reader.seek(0)  # Seek back to beginning

        while self.reader.tell() + 8 <= file_length:
            start_offset = self.reader.tell()

            # 1) Read box size
            size = read_int()
            if size < 8:
                raise ValueError(f"Invalid box size {size} at offset {start_offset}")

            # 2) Read box type (4 ASCII bytes)
            type_bytes = read_fully(4)
            box_type = type_bytes.decode('ascii')

            # Record it
            self.current_box = Box(type=box_type, offset=start_offset, size=size)

            # 3) Handle 'moov' or 'moof'
            payload_size = size - 8
            payload = read_fully(payload_size)

            if box_type == "moov":
                self.parse_moov(payload)
            elif box_type == "moof":
                self.moofs.append(Box(type=box_type, offset=start_offset, size=size))
                self.count_samples_in_moof(payload)

            # 4) Skip to next box (in case box handler didn't consume the stream)
            self.reader.seek(start_offset + size)

    def count_samples_in_moof(self, moof_data: bytes) -> int:

        buffer = BytesIO(moof_data)
        sample_count = 0

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        while buffer.tell() + 8 <= len(moof_data):
            start_pos = buffer.tell()

            size = read_uint32()
            type_bytes = buffer.read(4)
            box_type = type_bytes.decode('ascii')

            if box_type == "traf":
                traf_end = start_pos + size
                while buffer.tell() + 8 <= traf_end:
                    box_start = buffer.tell()

                    sub_size = read_uint32()
                    sub_type = buffer.read(4).decode('ascii')

                    if sub_type == "trun":
                        if sub_size >= 12:
                            buffer.read(4)  # skip version & flags
                            count = read_uint32()
                            sample_count += count
                            buffer.seek(box_start + sub_size)
                        else:
                            break  # malformed trun
                    else:
                        buffer.seek(box_start + sub_size)
            else:
                buffer.seek(start_pos + size)

        self.total_samples_from_moof += sample_count
        return sample_count

    def parse_moov(self, payload: bytes):

        buffer = BytesIO(payload)

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        while buffer.tell() + 8 <= len(payload):
            box_start = buffer.tell()
            box_size = read_uint32()
            box_type = read_uint32()

            # Slice the buffer to pass only box payload
            box_payload = payload[box_start + 8: box_start + box_size]

            if box_type == 0x6D766864:  # "mvhd"
                self.parse_mvhd(box_payload)
            elif box_type == 0x7472616B:  # "trak"
                self.parse_trak(box_payload)

            buffer.seek(box_start + box_size)

    def parse_mvhd(self, data: bytes):

        buffer = BytesIO(data)

        def read_uint8():
            return int.from_bytes(buffer.read(1), 'big')

        def read_uint16():
            return int.from_bytes(buffer.read(2), 'big')

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        def read_uint64():
            return int.from_bytes(buffer.read(8), 'big')

        version = read_uint8()
        buffer.read(3)  # skip flags (3 bytes)

        if version == 1:
            _ = read_uint64()  # creation_time
            _ = read_uint64()  # modification_time
            self.movie_timescale = read_uint32()
            self.movie_duration = read_uint64()
        else:
            _ = read_uint32()  # creation_time
            _ = read_uint32()  # modification_time
            self.movie_timescale = read_uint32()
            self.movie_duration = read_uint32()

        _ = read_uint32()  # rate
        _ = read_uint16()  # volume

        # Skip reserved (10 bytes) + matrix (36 bytes) + pre_defined (24 bytes)
        buffer.read(10 + 36 + 24)

    def parse_trak(self, data: bytes):
        buffer = BytesIO(data)

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        while buffer.tell() + 8 <= len(data):
            box_start = buffer.tell()
            box_size = read_uint32()
            box_type = read_uint32()

            box_payload = data[box_start + 8: box_start + box_size]

            if box_type == self.ATOM_MDIA:
                self.parse_mdia(box_payload)
            elif box_type == self.ATOM_TKHD:
                self.parse_tkhd(box_payload)

            buffer.seek(box_start + box_size)

    def parse_tkhd(self, data: bytes):

        buffer = BytesIO(data)

        def read_uint8():
            return int.from_bytes(buffer.read(1), 'big')

        def read_uint16():
            return int.from_bytes(buffer.read(2), 'big')

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        def read_uint64():
            return int.from_bytes(buffer.read(8), 'big')

        version = read_uint8()
        flags = (read_uint8() << 16) | (read_uint8() << 8) | read_uint8()

        remaining = lambda: len(data) - buffer.tell()

        if version == 1:
            if remaining() < 32:
                return
            buffer.read(8 + 8)  # creation_time + modification_time
            track_id = read_uint32()
            buffer.read(4)  # reserved
            self.track_duration = read_uint64()
        else:
            if remaining() < 20:
                return
            buffer.read(4 + 4)  # creation_time + modification_time
            track_id = read_uint32()
            buffer.read(4)  # reserved
            self.track_duration = read_uint32() & 0xFFFFFFFF

        # Skip reserved(8), layer/group/volume(8), matrix(36), width+height(8)
        skip_bytes = 8 + 2 + 2 + 2 + 2 + 36 + 4 + 4
        if remaining() >= skip_bytes:
            buffer.read(skip_bytes)
        else:
            buffer.seek(len(data))

    def parse_mdia(self, data: bytes):
        buffer = BytesIO(data)

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        while buffer.tell() + 8 <= len(data):
            box_start = buffer.tell()
            box_size = read_uint32()
            box_type = read_uint32()

            box_payload = data[box_start + 8: box_start + box_size]

            if box_type == 0x6D646864:  # "mdhd"
                self.parse_mdhd(box_payload)
            elif box_type == 0x68646C72:  # "hdlr"
                self.parse_hdlr(box_payload)
            elif box_type == 0x6D696E66:  # "minf"
                self.parse_minf(box_payload)

            buffer.seek(box_start + box_size)

    def parse_mdhd(self, data: bytes):
        buffer = BytesIO(data)

        def read_uint8():
            return int.from_bytes(buffer.read(1), 'big')

        def read_uint16():
            return int.from_bytes(buffer.read(2), 'big')

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        def read_uint64():
            return int.from_bytes(buffer.read(8), 'big')

        version = read_uint8()
        buffer.read(3)  # skip flags

        if version == 1:
            buffer.read(8)  # creation_time
            buffer.read(8)  # modification_time
            self.media_timescale = read_uint32()
            self.media_duration = read_uint64()
        else:
            buffer.read(4)  # creation_time
            buffer.read(4)  # modification_time
            self.media_timescale = read_uint32()
            self.media_duration = read_uint32()

        lang_code = read_uint16()
        self.language = self.decode_language(lang_code)

    def decode_language(self, code: int) -> str:
        return ''.join([
            chr(((code >> 10) & 0x1F) + 0x60),
            chr(((code >> 5) & 0x1F) + 0x60),
            chr((code & 0x1F) + 0x60)
        ])

    def parse_hdlr(self, data: bytes):
        buffer = BytesIO(data)

        buffer.read(4)  # version + flags
        buffer.read(4)  # pre_defined
        handler = buffer.read(4)
        self.handler_type = handler.decode('ascii')

    def parse_minf(self, data: bytes):
        buffer = BytesIO(data)

        def read_uint32():
            return int.from_bytes(buffer.read(4), 'big')

        while buffer.tell() + 8 <= len(data):
            box_start = buffer.tell()
            box_size = read_uint32()
            box_type = read_uint32()

            box_payload = data[box_start + 8: box_start + box_size]

            if box_type == 0x7374626C:  # "stbl"
                self.parse_stbl(BytesIO(box_payload))

            buffer.seek(box_start + box_size)

    def parse_stbl(self, data: BytesIO):
        while data.getbuffer().nbytes - data.tell() >= 8:
            box_start = data.tell()
            box_size = int.from_bytes(data.read(4), byteorder='big')
            box_type = data.read(4).decode('utf-8')

            if box_type == "stsd":
                data.seek(box_start)
                self.stsd_box = data.read(box_size)
                break

            data.seek(box_start + box_size)

    def get_samples(self, initial_chunk: bool) -> list:
        self.entries.clear()
        target_samples = 2 if initial_chunk else 6

        while self.current_moof_index < len(self.moofs):
            current_moof = self.moofs[self.current_moof_index]
            moof_end = current_moof.offset + current_moof.size
            moof_payload_start = current_moof.offset + 8

            while moof_payload_start + 8 < moof_end:
                self.reader.seek(moof_payload_start)
                box_header = self.reader.read(8)
                inner_box_size = struct.unpack(">I", box_header[0:4])[0]
                inner_box_type = box_header[4:8].decode('ascii')

                if inner_box_type == "traf":
                    traf_start = self.reader.tell()
                    traf_end = traf_start + (inner_box_size - 8)

                    while self.reader.tell() + 8 <= traf_end:
                        inner_header = self.reader.read(8)
                        inner_size = struct.unpack(">I", inner_header[0:4])[0]
                        inner_type = inner_header[4:8].decode('ascii')

                        if inner_type == "trun":
                            version_and_flags = self.reader.read(4)
                            version = version_and_flags[0]
                            flags = (
                                    (version_and_flags[1] << 16) |
                                    (version_and_flags[2] << 8) |
                                    version_and_flags[3]
                            )

                            sample_count = struct.unpack(">I", self.reader.read(4))[0]

                            data_offset = struct.unpack(">i", self.reader.read(4))[0] if (flags & 0x000001) else 0

                            has_duration = (flags & 0x000100) != 0
                            has_size = (flags & 0x000200) != 0
                            has_flags = (flags & 0x000400) != 0
                            has_cto = (flags & 0x000800) != 0

                            default_duration = 1024
                            default_size = 0
                            default_flags = 0

                            start_index = self.last_retrieved_sample_index+1
                            sample_offset_start = current_moof.offset + data_offset
                            sample_offset = sample_offset_start

                            for i in range(sample_count):
                                duration = struct.unpack(">I", self.reader.read(4))[
                                    0] if has_duration else default_duration
                                size = struct.unpack(">I", self.reader.read(4))[0] if has_size else default_size
                                flags_per_sample = struct.unpack(">I", self.reader.read(4))[
                                    0] if has_flags else default_flags
                                cto = struct.unpack(">i", self.reader.read(4))[0] if has_cto else 0

                                is_keyframe = (flags_per_sample & 0x00010000) == 0

                                if i < start_index:
                                    sample_offset += size
                                    continue

                                self.entries.append(TrunSampleEntry(
                                    index=i,
                                    size=size,
                                    offset=sample_offset,
                                    duration=duration,
                                    flags=flags_per_sample,
                                    composition_time_offset=cto,
                                    is_sync_sample=is_keyframe
                                ))

                                sample_offset += size
                                self.last_retrieved_sample_index+= 1

                                if len(self.entries) >= target_samples:
                                    return self.entries

                            self.current_moof_index += 1
                            self.last_retrieved_sample_index=-1

                        # Skip the rest of the box if not "trun"
                        self.reader.seek(self.reader.tell() + (inner_size - 8))

                moof_payload_start += inner_box_size

        return self.entries[:target_samples] if len(self.entries) > target_samples else self.entries


