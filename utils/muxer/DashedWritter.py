import struct
from pathlib import Path

from utils.muxer import mp4utils
from utils.muxer.mp4utils import write_ftyp


class DashedWriter:
    def __init__(self, file_path: Path, sources: list,callback):
        self.file = open(file_path, "wb+")
        self.sources = sources
        self.callback = callback

    def build_non_fmp4(self):
        ftyp = write_ftyp()
        self.file.seek(0)
        self.file.write(ftyp)

        total_samples = sum(source.total_samples_from_moof for source in self.sources)
        moov_reserved_size = mp4utils.estimate_moov_size(total_samples)
        moov_position = self.file.tell()
        self.file.write(b"\x00" * moov_reserved_size)

        self.write_mdat()



        # write_mdat()

        trak_list = []
        for source in self.sources:
            stsc = mp4utils.write_stsc(source.samples_per_chunk_list)
            stsz = mp4utils.write_stsz(source.samples_sizes)
            stco = mp4utils.write_stco(source.chunks_offsets)

            dref_entry = struct.pack(">I4sI", 12, b'url ', 1)
            dref_box = struct.pack(">I4sII", 28, b'dref', 0, 1) + dref_entry

            dinf_box = struct.pack(">I4s", 36, b'dinf') + dref_box

            hdlr = mp4utils.write_hdlr(source.handler_type)

            if source.handler_type == "soun":
                stts = mp4utils.write_stts(len(source.samples_sizes), 1024)
                stbl = mp4utils.write_stbl(source.stsd_box, stts, stsc, stsz, stco)
                vmhd = mp4utils.write_vmhd("smhd")
            else:
                stts = mp4utils.write_stts(len(source.samples_sizes), 512)
                stss = mp4utils.write_stss(source.key_samples_indices)
                ctts = mp4utils.write_ctts(source.ctts_entries)
                stbl = mp4utils.write_stbl(source.stsd_box, stts, stsc, stsz, stco, stss, ctts)
                vmhd = mp4utils.write_vmhd("vmhd")

            minf = mp4utils.write_minf(vmhd, dinf_box, stbl)
            mdhd = mp4utils.write_mdhd(source.media_timescale, int(source.media_duration))
            mdia = mp4utils.write_mdia(mdhd, hdlr, minf)
            tkhd = mp4utils.write_tkhd(int(source.track_duration))
            trak = mp4utils.write_trak(tkhd, mdia)
            trak_list.append(trak)

        movie_timescale = 1000
        max_track = max(self.sources, key=lambda s: s.track_duration / s.media_timescale)
        mvhd_duration = int(max_track.track_duration * movie_timescale / max_track.media_timescale)
        mvhd = mp4utils.write_mvhd(movie_timescale, mvhd_duration, len(self.sources) + 1)
        moov_box = mp4utils.write_moov(mvhd, trak_list)


        self.file.seek(moov_position)
        self.file.write(moov_box)
        self.file.close()

    def write_mdat(self):
        mdat_start = self.file.tell()



        # Write placeholder for size + 'mdat'
        self.file.write(struct.pack(">I4s", 0, b'mdat'))

        ts = sum(source.total_samples_from_moof for source in self.sources)

        while True:
            sources_done = 0

            for source in self.sources:
                samples = source.get_samples(source.initial_chunk)
                source.initial_chunk = False

                if samples:
                    source.chunks_offsets.append(self.file.tell())
                    source.samples_per_chunk_list.append(len(samples))  # ✅ TRACK CHUNK SIZE

                    for sample in samples:
                        source.reader.seek(sample.offset)
                        data = source.reader.read(sample.size)
                        self.file.write(data)

                        source.samples_sizes.append(sample.size)

                        if source.handler_type == "vide":
                            if sample.is_sync_sample:
                                source.key_samples_indices.append(len(source.samples_sizes) - 1)

                            cto = sample.composition_time_offset
                            if source.last_offset is None:
                                source.last_offset = cto
                                source.run_length = 1
                            elif cto == source.last_offset:
                                source.run_length += 1
                            else:
                                source.ctts_entries.append((source.run_length, source.last_offset))
                                source.last_offset = cto
                                source.run_length = 1

                        self.callback(f"{len(source.samples_sizes)}/{ts} Written Samples")

                else:
                    sources_done += 1
                    if source.last_offset is not None and source.run_length > 0:
                        source.ctts_entries.append((source.run_length, source.last_offset))


            if sources_done == len(self.sources):
                break

        mdat_end = self.file.tell()
        size_long = mdat_end - mdat_start
        assert size_long <= 0xFFFFFFFF, f"mdat too large: {size_long} bytes"

        # Seek back and write actual mdat size
        self.file.seek(mdat_start)
        self.file.write(struct.pack(">I", size_long))  # Update size
        self.file.seek(mdat_end)



