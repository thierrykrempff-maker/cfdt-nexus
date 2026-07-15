"""Pure, deterministic chunking rules for Protection sociale LOT 1D."""
from __future__ import annotations

from dataclasses import dataclass
import math
import re

PAGE_SEPARATOR = re.compile(r"(?m)^---\s+PAGE\s+(.+?)\s+---$")
TABLE_SEPARATOR = re.compile(r"(?m)^---\s+TABLE\s+(.+?)\s+---$")
PARAGRAPH_SEPARATOR = re.compile(r"(?m)^---\s+PARAGRAPH\s+(.+?)\s+---$")


@dataclass(frozen=True)
class ChunkConfig:
    target_chars: int = 1600
    max_chars: int = 2500
    min_chars: int = 300
    overlap_chars: int = 200

    def validate(self) -> None:
        if not 1 <= self.target_chars <= self.max_chars:
            raise ValueError("target_chars must be between 1 and max_chars")
        if self.min_chars < 0 or self.overlap_chars < 0:
            raise ValueError("sizes must be non-negative")
        if self.overlap_chars >= self.max_chars:
            raise ValueError("overlap_chars must be smaller than max_chars")


def estimate_tokens(text: str) -> int:
    """Approximate locally as one token per four Unicode characters."""
    return math.ceil(len(text) / 4) if text else 0


def preferred_cut(text: str, start: int, maximum: int, target: int) -> tuple[int, bool]:
    """Return a Unicode-safe cut offset, preferring structural boundaries."""
    end = min(len(text), start + maximum)
    if end == len(text):
        return end, False
    floor = min(end - 1, start + max(1, target // 2))
    desired = min(end, start + target)
    patterns = (
        r"(?m)^---\s+PAGE\s+.+?\s+---$\n?",
        r"(?m)^---\s+TABLE\s+.+?\s+---$\n?",
        r"\n\n+",
        r"(?m)^---\s+PARAGRAPH\s+.+?\s+---$\n?",
        r"(?<=[.!?])\s+",
        r"(?<=[;:])\s+",
        r"\n",
        r"\s+",
    )
    for upper in (desired, end):
        window = text[floor:upper]
        for pattern in patterns:
            matches = list(re.finditer(pattern, window))
            if matches:
                return floor + matches[-1].end(), False
    return end, True


def split_ranges(text: str, config: ChunkConfig) -> list[tuple[int, int, bool]]:
    config.validate()
    ranges: list[tuple[int, int, bool]] = []
    start = 0
    while start < len(text):
        end, strict = preferred_cut(text, start, config.max_chars, config.target_chars)
        ranges.append((start, end, strict))
        start = end
    return ranges


def overlap_start(text: str, core_start: int, requested: int, previous_start: int) -> int:
    if requested <= 0 or core_start <= previous_start:
        return core_start
    candidate = max(previous_start, core_start - requested)
    tail = text[candidate:core_start]
    boundaries = list(re.finditer(r"(?<=[.!?])\s+|\n", tail))
    if boundaries:
        adjusted = candidate + boundaries[0].end()
        if core_start - adjusted >= requested // 2:
            return adjusted
    return candidate


def locator_data(text: str, start: int, end: int) -> tuple[list[int], list[int], list[int], list[str], str]:
    prefix = text[:start]
    pages = [int(x) for x in re.findall(r"(?m)^---\s+PAGE\s+(\d+)\s+---$", prefix + text[start:end])]
    current = re.findall(r"(?m)^---\s+PAGE\s+(\d+)\s+---$", prefix)
    if current:
        pages.append(int(current[-1]))
    paragraphs = list(range(prefix.count("\n\n") + 1, (prefix + text[start:end]).count("\n\n") + 2))
    tables = list(range(len(TABLE_SEPARATOR.findall(prefix)) + 1, len(TABLE_SEPARATOR.findall(prefix + text[start:end])) + 1))
    sections = [f"page:{value}" for value in sorted(set(pages))]
    chunk_type = "table" if tables else ("page" if pages else "paragraph" if "\n\n" in text[start:end] else "text")
    return sorted(set(pages)), paragraphs, tables, sections, chunk_type
