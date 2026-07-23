"""Explicit translation tables for payroll metadata and quality labels."""

from __future__ import annotations

from automation.contracts import (
    ConfidenceLevel as PayrollConfidenceLevel,
    ConfidentialityLevel as PayrollConfidentialityLevel,
    CriticalityLevel,
    ExpertReport,
    ReportStatus,
    SourceCategory,
)
from NEXUS_CORE import (
    ConfidenceLevel,
    ConfidenceScore,
    ConfidentialityLevel,
    DataSensitivity,
    DocumentType,
    EvidenceQuality,
    FindingSeverity,
    MetadataEntry,
    RedactionStatus,
    SourceType,
    ValidationStatus,
)


class PayrollMetadataMapper:
    """Centralize every legacy-to-Core vocabulary correspondence."""

    _CONFIDENTIALITY = {
        PayrollConfidentialityLevel.PUBLIC: ConfidentialityLevel.PUBLIC,
        PayrollConfidentialityLevel.INTERNAL: ConfidentialityLevel.INTERNAL,
        PayrollConfidentialityLevel.RESTRICTED: ConfidentialityLevel.RESTRICTED,
        PayrollConfidentialityLevel.SENSITIVE: ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
    }
    _CONFIDENCE = {
        PayrollConfidenceLevel.VERY_LOW: (0.2, ConfidenceLevel.LOW),
        PayrollConfidenceLevel.LOW: (0.35, ConfidenceLevel.LOW),
        PayrollConfidenceLevel.MEDIUM: (0.5, ConfidenceLevel.MEDIUM),
        PayrollConfidenceLevel.HIGH: (0.75, ConfidenceLevel.HIGH),
        PayrollConfidenceLevel.VERY_HIGH: (0.9, ConfidenceLevel.VERIFIED),
    }
    _SEVERITY = {
        CriticalityLevel.LOW: FindingSeverity.LOW,
        CriticalityLevel.MEDIUM: FindingSeverity.MEDIUM,
        CriticalityLevel.HIGH: FindingSeverity.HIGH,
        CriticalityLevel.CRITICAL: FindingSeverity.CRITICAL,
    }
    _SOURCE_TYPE = {
        SourceCategory.OFFICIAL: SourceType.OFFICIAL_WEBSITE,
        SourceCategory.REGULATORY: SourceType.LEGAL_DATABASE,
        SourceCategory.INTERNAL: SourceType.INTERNAL_REFERENTIAL,
        SourceCategory.CONTEXTUAL: SourceType.UNKNOWN,
        SourceCategory.OTHER: SourceType.UNKNOWN,
    }

    def confidence(self, report: ExpertReport) -> ConfidenceScore:
        assessment = next(
            (item for item in report.confidence_assessments if item.level is not None),
            None,
        )
        if assessment is None:
            return ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN)
        default_score, core_level = self._CONFIDENCE[assessment.level]
        return ConfidenceScore(
            assessment.score if assessment.score is not None else default_score,
            core_level,
        )

    def confidentiality(
        self, value: PayrollConfidentialityLevel
    ) -> ConfidentialityLevel:
        return self._CONFIDENTIALITY[value]

    def severity(self, value: CriticalityLevel) -> FindingSeverity:
        return self._SEVERITY[value]

    def source_type(self, category: SourceCategory, source_type: str) -> SourceType:
        explicit = {
            "official_api": SourceType.OFFICIAL_API,
            "legal_database": SourceType.LEGAL_DATABASE,
            "internal_referential": SourceType.INTERNAL_REFERENTIAL,
        }
        return explicit.get(source_type.lower(), self._SOURCE_TYPE[category])

    @staticmethod
    def document_type(source_type: str) -> DocumentType:
        normalized = source_type.lower()
        explicit = {
            "payslip": DocumentType.PAYSLIP,
            "bulletin_de_paie": DocumentType.PAYSLIP,
            "kelio": DocumentType.KELIO_EXPORT,
            "kelio_export": DocumentType.KELIO_EXPORT,
            "nibelis": DocumentType.NIBELIS_EXPORT,
            "nibelis_export": DocumentType.NIBELIS_EXPORT,
            "collective_agreement": DocumentType.COLLECTIVE_AGREEMENT,
            "accord_collectif": DocumentType.COLLECTIVE_AGREEMENT,
            "legal_text": DocumentType.LEGAL_TEXT,
            "texte_legal": DocumentType.LEGAL_TEXT,
        }
        return explicit.get(normalized, DocumentType.OTHER)

    @staticmethod
    def quality(report: ExpertReport) -> EvidenceQuality:
        return {
            ReportStatus.COMPLETED: EvidenceQuality.CONSISTENT,
            ReportStatus.PARTIAL: EvidenceQuality.INCOMPLETE,
            ReportStatus.DRAFT: EvidenceQuality.INCOMPLETE,
            ReportStatus.REFUSED: EvidenceQuality.UNKNOWN,
            ReportStatus.FAILED: EvidenceQuality.UNKNOWN,
        }[report.status]

    @staticmethod
    def validation(report: ExpertReport) -> ValidationStatus:
        return {
            ReportStatus.COMPLETED: ValidationStatus.VALID,
            ReportStatus.PARTIAL: ValidationStatus.PENDING,
            ReportStatus.DRAFT: ValidationStatus.PENDING,
            ReportStatus.REFUSED: ValidationStatus.INVALID,
            ReportStatus.FAILED: ValidationStatus.INVALID,
        }[report.status]

    @staticmethod
    def sensitive_text(field_code: str, value: str) -> MetadataEntry:
        return MetadataEntry(
            field_code,
            value,
            DataSensitivity.SENSITIVE,
            RedactionStatus.REDACTED,
        )
