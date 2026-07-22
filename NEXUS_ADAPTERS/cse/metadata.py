"""Explicit CSE Memory to Nexus Core metadata vocabulary."""

from __future__ import annotations

from datetime import datetime

from automation.cse_memory.metadata_models import MetadataRecord
from NEXUS_CORE import (
    ConfidenceLevel, ConfidenceScore, DataSensitivity, EvidenceQuality, MetadataEntry,
    RedactionStatus, ValidationStatus,
)
from NEXUS_CORE.reasoning import ConfidenceAssessment, ReasoningConfidence


class CSEMetadataMapper:
    @staticmethod
    def sensitive(key: str, value: str | int | float | bool | None) -> MetadataEntry:
        return MetadataEntry(key, value, DataSensitivity.SENSITIVE, RedactionStatus.REDACTED)

    @staticmethod
    def technical(key: str, value: str | int | float | bool | None) -> MetadataEntry:
        return MetadataEntry(key, value, DataSensitivity.NON_SENSITIVE, RedactionStatus.NOT_REQUIRED)

    @staticmethod
    def confidence(value: float) -> ConfidenceScore:
        score = max(0.0, min(1.0, value))
        if score >= 0.85:
            level = ConfidenceLevel.VERIFIED
        elif score >= 0.7:
            level = ConfidenceLevel.HIGH
        elif score >= 0.4:
            level = ConfidenceLevel.MEDIUM
        elif score > 0:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.UNKNOWN
        return ConfidenceScore(score, level)

    @staticmethod
    def quality(status: str) -> EvidenceQuality:
        return {
            "extracted": EvidenceQuality.CONSISTENT,
            "extracted_with_warnings": EvidenceQuality.INCOMPLETE,
        }.get(status, EvidenceQuality.UNKNOWN)

    @staticmethod
    def validation(status: str) -> ValidationStatus:
        return {
            "extracted": ValidationStatus.VALID,
            "extracted_with_warnings": ValidationStatus.PENDING,
        }.get(status, ValidationStatus.INVALID)

    def assessment(self, records: tuple[MetadataRecord, ...], evidence_count: int,
                   conflict_count: int) -> ConfidenceAssessment:
        values = [
            item.confidence
            for record in records
            for item in record.metadata.values()
            if isinstance(item.confidence, (int, float))
        ]
        score = sum(values) / len(values) if values else 0.0
        score = max(0.0, min(1.0, score))
        if score >= 0.8:
            level = ReasoningConfidence.HIGH
        elif score >= 0.5:
            level = ReasoningConfidence.MODERATE
        elif score > 0:
            level = ReasoningConfidence.LIMITED
        else:
            level = ReasoningConfidence.INSUFFICIENT
        return ConfidenceAssessment(
            level, self.confidence(score), evidence_count, 0, conflict_count, 0,
            ("CSE_METADATA_CONFIDENCE",),
        )

    @staticmethod
    def parsed_datetime(value: str, fallback: datetime) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo is not None else fallback
        except (TypeError, ValueError):
            return fallback
