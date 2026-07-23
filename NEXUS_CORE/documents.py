"""Document references and descriptive metadata only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .identifiers import DocumentId
from .privacy import ConfidentialityLevel, MetadataEntry
from .provenance import SourceReference


class DocumentType(str, Enum):
    EMPLOYMENT_CONTRACT = "employment_contract"
    EMPLOYMENT_AMENDMENT = "employment_amendment"
    PAYSLIP = "payslip"
    CAREER_STATEMENT = "career_statement"
    KELIO_EXPORT = "kelio_export"
    NIBELIS_EXPORT = "nibelis_export"
    CSE_MINUTES = "cse_minutes"
    CSSCT_MINUTES = "cssct_minutes"
    COLLECTIVE_AGREEMENT = "collective_agreement"
    LEGAL_TEXT = "legal_text"
    CASE_LAW = "case_law"
    SOCIAL_PROTECTION_NOTICE = "social_protection_notice"
    GUARANTEE_TABLE = "guarantee_table"
    MEDICAL_OR_HEALTH_DOCUMENT = "medical_or_health_document"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class DocumentSource:
    reference: SourceReference


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    document_type: DocumentType
    title: str | None = None
    publication_date: date | None = None
    language: str | None = None
    entries: tuple[MetadataEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentReference:
    document_id: DocumentId
    document_type: DocumentType
    source: DocumentSource
    metadata: DocumentMetadata
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.INTERNAL
