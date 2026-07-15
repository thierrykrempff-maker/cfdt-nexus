"""Traceable metadata models for CSE Memory Engine LOT 1C."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0"
EXTRACTION_VERSION = "1.0"

@dataclass
class MetadataValue:
    value: Any = None
    confidence: float = 0.0
    confidence_level: str = "very_low"
    detected_from: list[str] = field(default_factory=list)
    evidence_type: str | None = None
    rule_id: str | None = None
    alternatives: list[Any] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class MetadataRecord:
    metadata_record_id: str
    document_id: str
    source_document_id: str
    source_relative_path: str
    source_sha256: str
    metadata_schema_version: str
    extraction_version: str
    extraction_status: str
    extracted_at: str
    warnings: list[str]
    conflicts: list[dict[str, Any]]
    evidence_summary: dict[str, int]
    metadata: dict[str, MetadataValue]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
