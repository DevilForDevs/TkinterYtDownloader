from dataclasses import dataclass
from typing import Optional


@dataclass
class Box:
    type: str = ""
    offset: int = 0  # Kotlin's Long → Python int
    size: int = 0

@dataclass
class TrunSampleEntry:
    index: int
    size: int
    offset: int
    duration: Optional[int] = None
    flags: Optional[int] = None
    composition_time_offset: Optional[int] = None
    is_sync_sample: bool = True