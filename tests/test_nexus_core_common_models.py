"""Behavioral boundaries of the minimal Nexus Core domain language."""

from dataclasses import fields
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from NEXUS_CORE import (
    AcquisitionMethod,
    AnalysisId,
    AnalysisQuestion,
    AnalysisReport,
    AnalysisRequest,
    AnalysisScope,
    AnalysisStatus,
    BooleanEvidenceValue,
    ConfidenceLevel,
    ConfidenceScore,
    ConflictId,
    ConflictReason,
    CorrelationId,
    CustomEvidenceValue,
    DataSensitivity,
    DocumentId,
    DocumentMetadata,
    DocumentReference,
    DocumentSource,
    DocumentType,
    DomainAnalysisResult,
    DomainResultReference,
    DomainSelection,
    EmployerReference,
    EmploymentPeriod,
    EmploymentReference,
    EntityId,
    EntityReference,
    Evidence,
    EvidenceConflict,
    EvidenceId,
    EvidenceQuality,
    Finding,
    FindingId,
    FindingSeverity,
    FindingStatus,
    FindingType,
    MetadataEntry,
    NumericEvidenceValue,
    Period,
    PeriodPrecision,
    PeriodStatus,
    PersonReference,
    Provenance,
    Recommendation,
    RecommendationId,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
    SourceReference,
    SourceType,
    TextEvidenceValue,
    ValidationStatus,
)


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)


def provenance() -> Provenance:
    return Provenance(
        source=SourceReference(EntityId("source-synthetic-1"), SourceType.SYNTHETIC_FIXTURE, "fixture"),
        acquisition_method=AcquisitionMethod.GENERATED,
        acquired_at=NOW,
    )


def evidence(identifier: str = "evidence-1") -> Evidence:
    return Evidence(
        evidence_id=EvidenceId(identifier),
        subject_reference=EntityReference(EntityId("subject-pseudo-1"), "person"),
        fact_type="employment_status",
        value=TextEvidenceValue("synthetic-value"),
        period=Period(date(2025, 1, 1), date(2025, 12, 31)),
        document_reference=None,
        provenance=provenance(),
        confidence=ConfidenceScore(0.8, ConfidenceLevel.HIGH),
        quality=EvidenceQuality.CONSISTENT,
        validation_status=ValidationStatus.VALID,
        produced_by=EntityId("producer-test-1"),
        metadata=(),
        created_at=NOW,
    )


def test_person_reference_is_pseudonymous_and_has_no_direct_identity_fields():
    person = PersonReference(EntityId("person-pseudo-42"))
    assert person.person_id.value == "person-pseudo-42"
    assert {item.name for item in fields(PersonReference)} == {"person_id", "confidentiality"}


@pytest.mark.parametrize(
    "direct_identifier",
    ["person@example.invalid", "299129999999901", "FR7630006000011234567890189"],
)
def test_technical_identifiers_reject_direct_personal_data(direct_identifier):
    with pytest.raises(ValueError, match="personal data"):
        EntityId(direct_identifier)


def test_open_period_overlap_and_containment_have_no_legal_inference():
    open_period = Period(date(2025, 1, 1), precision=PeriodPrecision.MONTH)
    nested = Period(date(2025, 2, 1), date(2025, 2, 28))
    disjoint = Period(date(2024, 1, 1), date(2024, 12, 31))
    assert open_period.status is PeriodStatus.OPEN
    assert open_period.overlaps(nested)
    assert open_period.contains(nested)
    assert not open_period.overlaps(disjoint)


def test_employment_period_composes_neutral_references():
    person = PersonReference(EntityId("person-pseudo-1"))
    employer = EmployerReference(EntityId("employer-reference-1"))
    employment = EmploymentReference(EntityId("employment-reference-1"), person, employer)
    model = EmploymentPeriod(employment, Period(date(2020, 1, 1)))
    assert model.period.status is PeriodStatus.OPEN


def test_document_reference_preserves_descriptive_source_and_metadata():
    source = SourceReference(EntityId("source-test-1"), SourceType.EMPLOYEE_DOCUMENT, "employee_upload")
    document = DocumentReference(
        DocumentId("document-test-1"),
        DocumentType.PAYSLIP,
        DocumentSource(source),
        DocumentMetadata(DocumentType.PAYSLIP, publication_date=date(2025, 1, 31)),
    )
    assert document.document_type is DocumentType.PAYSLIP
    assert document.source.reference == source


def test_confidence_is_technical_and_separate_from_evidence_quality():
    model = evidence()
    assert model.confidence == ConfidenceScore(0.8, ConfidenceLevel.HIGH)
    assert model.quality is EvidenceQuality.CONSISTENT
    assert not hasattr(model, "legal_weight")


@pytest.mark.parametrize(
    "typed_value",
    [
        TextEvidenceValue("synthetic"),
        NumericEvidenceValue(Decimal("12.50"), "hours"),
        BooleanEvidenceValue(True),
        CustomEvidenceValue("engine_extension", (MetadataEntry("code", "synthetic"),)),
    ],
)
def test_evidence_accepts_only_explicit_typed_value_families(typed_value):
    model = evidence()
    model = Evidence(**{item.name: getattr(model, item.name) for item in fields(model) if item.name != "value"}, value=typed_value)
    assert model.value.value_type
    assert model.period is not None
    assert model.provenance == provenance()
    assert model.confidence.level is ConfidenceLevel.HIGH


def test_evidence_value_annotation_is_not_any():
    assert Evidence.__annotations__["value"] == "EvidenceValueType"


@pytest.mark.parametrize(
    ("finding_type", "code"),
    [
        (FindingType.ANOMALY, "DATE_MISMATCH"),
        (FindingType.MISSING_DOCUMENT, "PAYSLIP_MISSING"),
    ],
)
def test_findings_are_neutral_classifications(finding_type, code):
    finding = Finding(
        FindingId(f"finding-{finding_type.value}"),
        finding_type,
        FindingSeverity.MEDIUM,
        FindingStatus.OPEN,
        code,
    )
    assert finding.finding_type is finding_type


def test_conflict_preserves_all_evidence_without_selected_value():
    conflict = EvidenceConflict(
        ConflictId("conflict-1"),
        (EvidenceId("evidence-1"), EvidenceId("evidence-2")),
        ConflictReason.VALUE_MISMATCH,
        Period(date(2025, 1, 1), date(2025, 1, 31)),
    )
    assert len(conflict.evidence_references) == 2
    assert not hasattr(conflict, "selected_value")
    assert conflict.resolution_reference is None


def test_verification_recommendation_is_not_a_legal_conclusion():
    recommendation = Recommendation(
        RecommendationId("recommendation-1"),
        RecommendationType.VERIFY_INFORMATION,
        RecommendationPriority.NORMAL,
        RecommendationStatus.PROPOSED,
        "VERIFY_PERIOD",
    )
    assert recommendation.recommendation_type is RecommendationType.VERIFY_INFORMATION
    assert not hasattr(recommendation, "legal_conclusion")


def test_multidomain_request_and_reference_only_report():
    request = AnalysisRequest(
        AnalysisId("analysis-1"),
        CorrelationId("correlation-1"),
        AnalysisQuestion("CHECK_SYNTHETIC_CASE"),
        AnalysisScope((EntityReference(EntityId("subject-pseudo-1"), "person"),)),
        (DomainSelection.PAYROLL, DomainSelection.RETIREMENT_PENIBILITY),
    )
    result = DomainAnalysisResult(DomainSelection.PAYROLL, AnalysisStatus.COMPLETED)
    report = AnalysisReport(
        request.analysis_id,
        AnalysisStatus.COMPLETED,
        domain_results=(
            DomainResultReference(EntityId("result-payroll-1"), result.domain, result.status),
            DomainResultReference(EntityId("result-retirement-1"), DomainSelection.RETIREMENT_PENIBILITY, AnalysisStatus.COMPLETED),
        ),
    )
    assert len(request.domains) == 2
    assert len(report.domain_results) == 2
    assert not hasattr(report, "merged_answer")
