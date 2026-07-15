"""Pure deterministic splitting rules for LOT 1D."""
from __future__ import annotations
from dataclasses import dataclass
import math, re

@dataclass(frozen=True)
class ChunkConfig:
    target_chars: int = 1600
    max_chars: int = 2500
    min_chars: int = 300
    overlap_chars: int = 200
    def validate(self) -> None:
        if not (1 <= self.target_chars <= self.max_chars): raise ValueError("target_chars must be between 1 and max_chars")
        if self.min_chars < 0 or self.overlap_chars < 0: raise ValueError("sizes must be non-negative")
        if self.overlap_chars >= self.max_chars: raise ValueError("overlap must be smaller than max_chars")

def estimate_tokens(text: str) -> int:
    """Local approximation: one token per four Unicode characters."""
    return math.ceil(len(text) / 4) if text else 0

def split_text(text: str, limit: int, target: int) -> list[tuple[str, bool]]:
    """Lossless split; boolean indicates a last-resort strict cut."""
    if len(text) <= limit: return [(text, False)]
    out=[]; pos=0
    patterns=(r"\n\n", r"(?<=[.!?])\s+", r"(?<=[;:])\s+", r"\n", r"\s+")
    while len(text)-pos > limit:
        window=text[pos:pos+limit]; floor=max(1, min(target, limit)//2); cut=0
        for pattern in patterns:
            matches=list(re.finditer(pattern, window[floor:]))
            if matches:
                cut=floor+matches[-1].end(); break
        strict=not bool(cut)
        if not cut: cut=limit
        out.append((text[pos:pos+cut], strict)); pos += cut
    if pos < len(text): out.append((text[pos:], False))
    return out

def overlap_prefix(previous: str, requested: int, room: int) -> str:
    size=min(requested, room, len(previous))
    if size <= 0: return ""
    tail=previous[-size:]
    match=re.search(r"(?<=[.!?])\s+", tail)
    if match and len(tail)-match.end() >= size//2: return tail[match.end():]
    return tail
