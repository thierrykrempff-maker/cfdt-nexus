"""Generic evidence preserving source, period, confidence and quality."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .documents import DocumentReference
from .entities import EntityReference
from .identifiers import EntityId, EvidenceId
from .periods import Period
from .privacy import ConfidentialityLevel, MetadataEntry
from .provenance import Provenance
from .quality import ConfidenceScore, EvidenceQuality, ValidationStatus
from .values import EvidenceValueType


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: EvidenceId
    subject_reference: EntityReference
    fact_type: str
    value: EvidenceValueType = field(repr=False)
    period: Period | None
    document_reference: DocumentReference | None
    provenance: Provenance
    confidence: ConfidenceScore
    quality: EvidenceQuality
    validation_status: ValidationStatus
    produced_by: EntityId
    metadata: tuple[MetadataEntry, ...]
    created_at: datetime
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.CONFIDENTIAL
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.fact_type or not self.fact_type.replace("_", "").isalnum():
            raise ValueError("fact_type must be a stable technical code")
