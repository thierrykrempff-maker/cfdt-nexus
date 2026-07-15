"""Normalized records for the local CSE document importer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_VERSION = "1.0"
VALID_STATUSES = {
    "extracted",
    "extracted_with_warnings",
    "unsupported",
    "converter_required",
    "empty",
    "unreadable",
    "failed",
}


@dataclass
class ExtractionResult:
    text_content: str = ""
    status: str = "extracted"
    extractor_name: str = "none"
    extractor_method: str = "not_attempted"
    page_count: int | None = None
    sheet_count: int | None = None
    slide_count: int | None = None
    paragraph_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DocumentRecord:
    document_id: str
    source_relative_path: str
    source_filename: str
    source_extension: str
    source_size_bytes: int
    source_sha256: str
    source_modified_at: str
    detected_year: str | None
    detected_family: str
    extractor_name: str
    extractor_method: str
    extraction_status: str
    extraction_error_code: str | None
    extraction_error_message: str | None
    text_content: str
    text_length: int
    page_count: int | None
    sheet_count: int | None
    slide_count: int | None
    paragraph_count: int | None
    technical_metadata: dict[str, Any]
    warnings: list[str]
    imported_at: str
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        if self.extraction_status not in VALID_STATUSES:
            raise ValueError(f"Invalid extraction status: {self.extraction_status}")
        return asdict(self)
