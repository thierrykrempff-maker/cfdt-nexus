"""Normalized text and block models for CSE Memory Engine LOT 1B."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


NORMALIZATION_VERSION = "1.0"
NORMALIZED_SCHEMA_VERSION = "1.0"


@dataclass
class TextBlock:
    block_id: str
    block_type: str
    ordinal: int
    source_locator: str | None
    text: str
    text_length: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class NormalizedDocument:
    document_id: str
    source_document_id: str
    source_relative_path: str
    source_sha256: str
    source_extraction_status: str
    normalization_status: str
    normalization_version: str
    original_text_length: int
    normalized_text_length: int
    normalized_text: str
    blocks: list[TextBlock]
    block_count: int
    page_count: int | None
    slide_count: int | None
    sheet_count: int | None
    detected_language_hint: str | None
    quality_score: int
    quality_level: str
    quality_flags: list[str]
    transformations_applied: list[str]
    removed_repeated_lines: list[str]
    warnings: list[str]
    normalized_at: str
    schema_version: str = NORMALIZED_SCHEMA_VERSION
    technical_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
