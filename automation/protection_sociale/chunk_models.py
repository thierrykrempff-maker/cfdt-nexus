"""Data models for Protection sociale LOT 1D technical chunks."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CHUNKING_VERSION = "1.0"
SCHEMA_VERSION = "1.0"


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
    source_section_ids: list[str] = field(default_factory=list)
    source_block_ids: list[str] = field(default_factory=list)
    source_start_offset: int = 0
    source_end_offset: int = 0
    page_numbers: list[int] = field(default_factory=list)
    paragraph_indexes: list[int] = field(default_factory=list)
    table_indexes: list[int] = field(default_factory=list)
    previous_chunk_id: str | None = None
    next_chunk_id: str | None = None
    overlap_previous_chars: int = 0
    overlap_next_chars: int = 0
    metadata_snapshot: dict[str, Any] = field(default_factory=dict)
    source_quality_level: str = "unusable"
    metadata_quality_level: str = "unusable"
    chunk_quality_score: int = 0
    chunk_quality_level: str = "unusable"
    quality_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_indexable: bool = True
    non_indexable_reason: str | None = None
    strategy_id: str = "protection_sociale_hybrid_v1"
    chunking_version: str = CHUNKING_VERSION
    created_at: str = ""
    schema_version: str = SCHEMA_VERSION
    duplicate_group_id: str | None = None
    content_id: str | None = None
    unique_text_length_chars: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
