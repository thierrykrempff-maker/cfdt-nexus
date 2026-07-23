"""Source and acquisition provenance without legal ranking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .identifiers import EntityId


class SourceType(str, Enum):
    EMPLOYEE_DOCUMENT = "employee_document"
    EMPLOYER_DOCUMENT = "employer_document"
    INTERNAL_REFERENTIAL = "internal_referential"
    OFFICIAL_API = "official_api"
    OFFICIAL_WEBSITE = "official_website"
    LEGAL_DATABASE = "legal_database"
    CSE_ARCHIVE = "cse_archive"
    SYNTHETIC_FIXTURE = "synthetic_fixture"
    MANUAL_ENTRY = "manual_entry"
    UNKNOWN = "unknown"


class AcquisitionMethod(str, Enum):
    UPLOAD = "upload"
    CONNECTOR = "connector"
    IMPORT = "import"
    MANUAL = "manual"
    GENERATED = "generated"
    RECONSTRUCTED = "reconstructed"


@dataclass(frozen=True, slots=True)
class SourceReference:
    source_id: EntityId
    source_type: SourceType
    label_code: str


@dataclass(frozen=True, slots=True)
class Provenance:
    source: SourceReference
    acquisition_method: AcquisitionMethod
    acquired_at: datetime
    trace_reference: EntityId | None = None
