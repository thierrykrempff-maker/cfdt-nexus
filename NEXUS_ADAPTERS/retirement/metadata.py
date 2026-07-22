"""Explicit retirement-to-Core vocabulary mappings."""

from __future__ import annotations

from datetime import date

from automation.contracts import ConfidenceLevel as ExpertConfidenceLevel, ExpertReport, ReportStatus
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import (
    EvidenceAuthorityLevel, EvidenceConfidenceLevel, EvidenceSourceType, EvidenceStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_import_models import ImportConfidence
from RETIREMENT_PENIBILITY_ENGINE.retirement_models import EvidenceGrade, RetirementConfidence
from NEXUS_CORE import (
    ConfidenceLevel, ConfidenceScore, DataSensitivity, DocumentType, EvidenceQuality,
    MetadataEntry, RedactionStatus, SourceType, ValidationStatus,
)


class RetirementMetadataMapper:
    """Central mapping table; no implicit enum or string conversion is allowed."""

    _CONFIDENCE = {
        EvidenceConfidenceLevel.UNKNOWN: ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN),
        EvidenceConfidenceLevel.LOW: ConfidenceScore(0.3, ConfidenceLevel.LOW),
        EvidenceConfidenceLevel.MEDIUM: ConfidenceScore(0.6, ConfidenceLevel.MEDIUM),
        EvidenceConfidenceLevel.HIGH: ConfidenceScore(0.85, ConfidenceLevel.HIGH),
    }
    _IMPORT_CONFIDENCE = {
        ImportConfidence.UNKNOWN: ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN),
        ImportConfidence.LOW: ConfidenceScore(0.3, ConfidenceLevel.LOW),
        ImportConfidence.MEDIUM: ConfidenceScore(0.6, ConfidenceLevel.MEDIUM),
        ImportConfidence.HIGH: ConfidenceScore(0.85, ConfidenceLevel.HIGH),
    }
    _REPORT_CONFIDENCE = {
        RetirementConfidence.UNKNOWN: ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN),
        RetirementConfidence.VERY_LOW: ConfidenceScore(0.15, ConfidenceLevel.LOW),
        RetirementConfidence.LOW: ConfidenceScore(0.3, ConfidenceLevel.LOW),
        RetirementConfidence.MEDIUM: ConfidenceScore(0.6, ConfidenceLevel.MEDIUM),
        RetirementConfidence.HIGH: ConfidenceScore(0.85, ConfidenceLevel.HIGH),
    }
    _DOCUMENT_TYPES = {
        EvidenceSourceType.OFFICIAL_RETIREMENT_RECORD: DocumentType.CAREER_STATEMENT,
        EvidenceSourceType.EMPLOYMENT_CONTRACT: DocumentType.EMPLOYMENT_CONTRACT,
        EvidenceSourceType.EMPLOYMENT_AMENDMENT: DocumentType.EMPLOYMENT_AMENDMENT,
        EvidenceSourceType.PAYSLIP: DocumentType.PAYSLIP,
        EvidenceSourceType.KELIO_EXPORT: DocumentType.KELIO_EXPORT,
        EvidenceSourceType.NIBELIS_EXPORT: DocumentType.NIBELIS_EXPORT,
        EvidenceSourceType.INEOS_AGREEMENT: DocumentType.COLLECTIVE_AGREEMENT,
        EvidenceSourceType.COLLECTIVE_AGREEMENT: DocumentType.COLLECTIVE_AGREEMENT,
        EvidenceSourceType.MEDICAL_OR_ATMP_NOTIFICATION: DocumentType.MEDICAL_OR_HEALTH_DOCUMENT,
        EvidenceSourceType.SOCIAL_SECURITY_DOCUMENT: DocumentType.SOCIAL_PROTECTION_NOTICE,
        EvidenceSourceType.CARSAT_NOTIFICATION: DocumentType.SOCIAL_PROTECTION_NOTICE,
        EvidenceSourceType.CNAV_NOTIFICATION: DocumentType.SOCIAL_PROTECTION_NOTICE,
        EvidenceSourceType.C2P_NOTIFICATION: DocumentType.SOCIAL_PROTECTION_NOTICE,
    }

    def evidence_confidence(self, value: EvidenceConfidenceLevel) -> ConfidenceScore:
        return self._CONFIDENCE[value]

    def import_confidence(self, value: ImportConfidence) -> ConfidenceScore:
        return self._IMPORT_CONFIDENCE[value]

    def report_confidence(self, value: RetirementConfidence) -> ConfidenceScore:
        return self._REPORT_CONFIDENCE[value]

    @staticmethod
    def expert_confidence(report: ExpertReport) -> ConfidenceScore:
        assessment = next((item for item in report.confidence_assessments if item.level), None)
        if assessment is None:
            return ConfidenceScore(0.0, ConfidenceLevel.UNKNOWN)
        defaults = {
            ExpertConfidenceLevel.VERY_LOW: (0.15, ConfidenceLevel.LOW),
            ExpertConfidenceLevel.LOW: (0.3, ConfidenceLevel.LOW),
            ExpertConfidenceLevel.MEDIUM: (0.5, ConfidenceLevel.MEDIUM),
            ExpertConfidenceLevel.HIGH: (0.75, ConfidenceLevel.HIGH),
            ExpertConfidenceLevel.VERY_HIGH: (0.9, ConfidenceLevel.VERIFIED),
        }
        default, level = defaults[assessment.level]
        return ConfidenceScore(assessment.score if assessment.score is not None else default, level)

    @staticmethod
    def expert_quality(report: ExpertReport) -> EvidenceQuality:
        return {
            ReportStatus.COMPLETED: EvidenceQuality.CONSISTENT,
            ReportStatus.PARTIAL: EvidenceQuality.INCOMPLETE,
            ReportStatus.DRAFT: EvidenceQuality.INCOMPLETE,
            ReportStatus.REFUSED: EvidenceQuality.UNKNOWN,
            ReportStatus.FAILED: EvidenceQuality.UNKNOWN,
        }[report.status]

    @staticmethod
    def expert_validation(report: ExpertReport) -> ValidationStatus:
        return {
            ReportStatus.COMPLETED: ValidationStatus.VALID,
            ReportStatus.PARTIAL: ValidationStatus.PENDING,
            ReportStatus.DRAFT: ValidationStatus.PENDING,
            ReportStatus.REFUSED: ValidationStatus.INVALID,
            ReportStatus.FAILED: ValidationStatus.INVALID,
        }[report.status]

    @staticmethod
    def confidence_from_grade(value: EvidenceGrade) -> ConfidenceScore:
        return {
            EvidenceGrade.A: ConfidenceScore(0.9, ConfidenceLevel.VERIFIED),
            EvidenceGrade.B: ConfidenceScore(0.75, ConfidenceLevel.HIGH),
            EvidenceGrade.C: ConfidenceScore(0.5, ConfidenceLevel.MEDIUM),
            EvidenceGrade.D: ConfidenceScore(0.3, ConfidenceLevel.LOW),
        }[value]

    @staticmethod
    def quality(authority: EvidenceAuthorityLevel) -> EvidenceQuality:
        return {
            EvidenceAuthorityLevel.AUTHORITATIVE_OFFICIAL: EvidenceQuality.CONSISTENT,
            EvidenceAuthorityLevel.AUTHORITATIVE_EMPLOYER: EvidenceQuality.CONSISTENT,
            EvidenceAuthorityLevel.CONTRACTUAL: EvidenceQuality.CONSISTENT,
            EvidenceAuthorityLevel.CORROBORATING: EvidenceQuality.CORROBORATED,
            EvidenceAuthorityLevel.CONTEXTUAL: EvidenceQuality.INCOMPLETE,
            EvidenceAuthorityLevel.DECLARATIVE_ONLY: EvidenceQuality.UNKNOWN,
        }[authority]

    @staticmethod
    def validation(status: EvidenceStatus) -> ValidationStatus:
        return {
            EvidenceStatus.VERIFIED: ValidationStatus.VALID,
            EvidenceStatus.PROVIDED: ValidationStatus.PENDING,
            EvidenceStatus.UNVERIFIED: ValidationStatus.PENDING,
            EvidenceStatus.CONTRADICTED: ValidationStatus.PENDING,
            EvidenceStatus.SUPERSEDED: ValidationStatus.INVALID,
            EvidenceStatus.EXPIRED: ValidationStatus.INVALID,
            EvidenceStatus.MISSING: ValidationStatus.INVALID,
            EvidenceStatus.RESTRICTED: ValidationStatus.PENDING,
            EvidenceStatus.REJECTED: ValidationStatus.INVALID,
        }[status]

    def document_type(self, value: EvidenceSourceType) -> DocumentType:
        return self._DOCUMENT_TYPES.get(value, DocumentType.OTHER)

    @staticmethod
    def source_type(value: EvidenceSourceType) -> SourceType:
        official = {EvidenceSourceType.OFFICIAL_RETIREMENT_RECORD, EvidenceSourceType.CARSAT_NOTIFICATION,
                    EvidenceSourceType.CNAV_NOTIFICATION, EvidenceSourceType.C2P_NOTIFICATION,
                    EvidenceSourceType.SOCIAL_SECURITY_DOCUMENT}
        employer = {EvidenceSourceType.EMPLOYMENT_CONTRACT, EvidenceSourceType.EMPLOYMENT_AMENDMENT,
                    EvidenceSourceType.PAYSLIP, EvidenceSourceType.EMPLOYER_CERTIFICATE,
                    EvidenceSourceType.KELIO_EXPORT, EvidenceSourceType.NIBELIS_EXPORT}
        if value in official:
            return SourceType.OFFICIAL_WEBSITE
        if value in employer:
            return SourceType.EMPLOYER_DOCUMENT
        return SourceType.INTERNAL_REFERENTIAL

    @staticmethod
    def metadata(key: str, value: str) -> MetadataEntry:
        return MetadataEntry(key, value, DataSensitivity.SENSITIVE, RedactionStatus.REDACTED)

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
