"""Models for deterministic, traceable LOT 1D chunks."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

CHUNKING_VERSION = "1.0"
CHUNK_SCHEMA_VERSION = "1.0"

@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    source_document_id: str
    metadata_record_id: str | None
    source_relative_path: str
    source_sha256: str
    chunk_index: int
    chunk_count: int
    chunk_type: str
    text: str
    text_length_chars: int
    estimated_token_count: int
    source_block_ids: list[str]
    source_block_start: str | None
    source_block_end: str | None
    source_locators: list[str]
    page_numbers: list[int]
    slide_numbers: list[int]
    sheet_names: list[str]
    previous_chunk_id: str | None
    next_chunk_id: str | None
    overlap_previous_chars: int
    overlap_next_chars: int
    metadata_snapshot: dict[str, Any]
    document_quality_level: str
    metadata_quality_level: str
    chunk_quality_score: int
    chunk_quality_level: str
    quality_flags: list[str]
    warnings: list[str]
    strategy_id: str = "hybrid_blocks_v1"
    chunking_version: str = CHUNKING_VERSION
    created_at: str = ""
    schema_version: str = CHUNK_SCHEMA_VERSION
    indexable: bool = True
    unique_text_length_chars: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
