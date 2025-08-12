from __future__ import annotations

import struct
import time

from typing import List


def write_stbl(*boxes: bytes) -> bytes:
    total_size = sum(len(b) for b in boxes) + 8
    return struct.pack(">I4s", total_size, b"stbl") + b"".join(boxes)

def write_stts(sample_count: int, sample_delta: int) -> bytes:
    return struct.pack(">I4sIIII",
                       24, b"stts", 0, 1,
                       sample_count, sample_delta)

def write_stsc(samples_per_chunk_list: List[int]) -> bytes:
    entries = []
    last_samples = -1
    for i, spc in enumerate(samples_per_chunk_list):
        if spc != last_samples:
            entries.append((i + 1, spc, 1))
            last_samples = spc

    box_size = 16 + 12 * len(entries)
    header = struct.pack(">I4sII", box_size, b"stsc", 0, len(entries))
    body = b''.join(struct.pack(">III", fc, spc, di) for fc, spc, di in entries)
    return header + body

def write_stsz(sizes: List[int]) -> bytes:
    entry_count = len(sizes)
    header = struct.pack(">I4sIII", 20 + 4 * entry_count, b"stsz", 0, 0, entry_count)
    body = b''.join(struct.pack(">I", size) for size in sizes)
    return header + body

def write_stco(offsets: list[int | float]) -> bytes:
    entry_count = len(offsets)
    header = struct.pack(">I4sII", 16 + 4 * entry_count, b"stco", 0, entry_count)
    body = b''.join(struct.pack(">I", int(offset)) for offset in offsets)
    return header + body

def write_stss(sync_sample_indices: list[int]) -> bytes:
    entry_count = len(sync_sample_indices)
    header = struct.pack(">I4sII", 16 + 4 * entry_count, b"stss", 0, entry_count)
    body = b''.join(struct.pack(">I", index + 1) for index in sync_sample_indices)
    return header + body

def write_ctts(entries: list[tuple[int, int]]) -> bytes:
    entry_count = len(entries)
    header = struct.pack(">I4sII", 16 + 8 * entry_count, b"ctts", 0, entry_count)
    body = b''.join(struct.pack(">II", count, offset) for count, offset in entries)
    return header + body


def write_mvhd(time_scale: int, duration: int, next_track: int) -> bytes:
    mac_time = int(time.time()) + 2082844800
    buffer = bytearray()
    buffer += struct.pack(">I4sB3s", 108, b"mvhd", 0x00, b"\x00\x00\x00")
    buffer += struct.pack(">IIII", mac_time, mac_time, time_scale, duration)
    buffer += struct.pack(">I", 0x00010000)         # rate = 1.0
    buffer += struct.pack(">H", 0x0100)             # volume = 1.0
    buffer += struct.pack(">H", 0)                  # reserved
    buffer += struct.pack(">II", 0, 0)              # reserved

    matrix = [
        0x00010000, 0, 0,
        0, 0x00010000, 0,
        0, 0, 0x40000000
    ]
    for val in matrix:
        buffer += struct.pack(">I", val)

    for _ in range(6):
        buffer += struct.pack(">I", 0)              # pre_defined

    buffer += struct.pack(">I", next_track)         # next_track_ID
    return bytes(buffer)


def write_trak(tkhd: bytes, mdia: bytes) -> bytes:
    content = tkhd + mdia
    size = len(content) + 8
    return struct.pack(">I4s", size, b"trak") + content


def write_tkhd(duration: int) -> bytes:
    mac_time = int(time.time()) + 2082844800
    buffer = bytearray()
    buffer += struct.pack(">I4sB3s", 92, b"tkhd", 0x00, b"\x00\x00\x07")
    buffer += struct.pack(">IIII", mac_time, mac_time, 1, 0)  # track_ID = 1
    buffer += struct.pack(">I", duration)
    buffer += struct.pack(">II", 0, 0)              # reserved

    buffer += struct.pack(">HH", 0, 0)              # layer & alternate group
    buffer += struct.pack(">H", 0x0100)             # volume
    buffer += struct.pack(">H", 0)                  # reserved

    matrix = [
        0x00010000, 0, 0,
        0, 0x00010000, 0,
        0, 0, 0x40000000
    ]
    for val in matrix:
        buffer += struct.pack(">I", val)

    buffer += struct.pack(">II", 0, 0)              # width & height (placeholders)
    return bytes(buffer)


def write_mdhd(time_scale: int, duration: int) -> bytes:
    mac_time = int(time.time()) + 2082844800
    buffer = bytearray()
    buffer += struct.pack(">I4sB3s", 32, b"mdhd", 0x00, b"\x00\x00\x00")
    buffer += struct.pack(">IIII", mac_time, mac_time, time_scale, duration)
    buffer += struct.pack(">H", 0x55c4)  # language = 'und'
    buffer += struct.pack(">H", 0)       # pre-defined
    return bytes(buffer)

def write_hdlr(handler_type: str) -> bytes:
    name = {
        "vide": "VideoHandler",
        "soun": "SoundHandler"
    }.get(handler_type, "UnknownHandler")

    name_bytes = name.encode("utf-8")
    name_length = len(name_bytes) + 1  # null-terminated
    size = 8 + 4 + 4 + 4 + 4 + 4 + 4 + name_length

    buffer = bytearray()
    buffer += struct.pack(">I4s", size, b"hdlr")
    buffer += struct.pack(">B3s", 0, b"\x00\x00\x00")  # version + flags
    buffer += struct.pack(">I", 0)  # pre_defined
    buffer += handler_type.encode("ascii").ljust(4, b"\x00")
    buffer += struct.pack(">III", 0, 0, 0)  # reserved
    buffer += name_bytes + b"\x00"  # name + null
    return bytes(buffer)


def write_mdia(mdhd: bytes, hdlr: bytes, minf: bytes) -> bytes:
    content = mdhd + hdlr + minf
    size = len(content) + 8
    return struct.pack(">I4s", size, b"mdia") + content


def write_minf(vmhd_or_smhd: bytes, dinf_box: bytes, stbl_box: bytes) -> bytes:
    content = vmhd_or_smhd + dinf_box + stbl_box
    size = len(content) + 8
    return struct.pack(">I4s", size, b"minf") + content


def write_vmhd(handler_type: str) -> bytes:
    buffer = bytearray()
    buffer += struct.pack(">I4s", 20, handler_type.encode("ascii"))
    buffer += struct.pack(">I", 0x00000001)  # version + flags
    buffer += struct.pack(">HHH", 0, 0, 0)   # graphicsmode, opcolor R, G
    buffer += struct.pack(">H", 0)           # opcolor B
    return bytes(buffer)


def write_moov(mvhd: bytes, tracks: list[bytes]) -> bytes:
    content = mvhd + b"".join(tracks)
    size = len(content) + 8
    return struct.pack(">I4s", size, b"moov") + content


def write_ftyp() -> bytes:
    major_brand = b"isom"
    minor_version = 0x200
    compatible_brands = [b"isom", b"iso2"]

    # Calculate size: 4 (size) + 4 (type) + 4 (major_brand) + 4 (minor_version)
    # + 4 * len(compatible_brands)
    size = 4 + 4 + 4 + 4 + 4 * len(compatible_brands)

    buffer = bytearray()
    buffer += struct.pack(">I4s", size, b"ftyp")
    buffer += struct.pack(">4sI", major_brand, minor_version)
    for brand in compatible_brands:
        buffer += struct.pack(">4s", brand)

    return bytes(buffer)


def estimate_moov_size(sample_count: int) -> int:
    base_moov = 1024   # mvhd + trak headers
    per_sample = 8     # estimated bytes per sample across tables
    estimated_size = base_moov + (sample_count * per_sample)
    return ((estimated_size + 4095) // 4096) * 4096  # round up to 4KB
