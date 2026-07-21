"""End-to-end conversion of an Expert Paie report into Nexus Core objects."""

from dataclasses import replace
from datetime import date, datetime, timezone

from automation.contracts import (
    ConfidenceAssessment as PayrollConfidenceAssessment,
    ConfidenceDimension,
    ConfidenceLevel as PayrollConfidenceLevel,
    ConfidentialityLevel as PayrollConfidentialityLevel,
    ConnectionStatus,
    ConsultationStatus,
    ExpertReport,
    KnowledgeSource,
    ReportStatus,
    SourceCategory,
    SourceEvidence,
)
from NEXUS_ADAPTERS.payroll import PayrollAdapter
from NEXUS_CORE import (
    ConfidenceLevel,
    DocumentType,
    EntityId,
    EntityReference,
    Period,
    SourceType,
)


NOW = datetime(2026, 7, 21, 17, 0, tzinfo=timezone.utc)
PERIOD = Period(date(2026, 1, 1), date(2026, 1, 31))
SUBJECT = EntityReference(EntityId("subject-payroll-adapter"), "person")


def source_pair():
    source = KnowledgeSource(
        "source-payroll-fixture",
        "Synthetic payroll source",
        "Synthetic publisher",
        SourceCategory.INTERNAL,
        "payslip",
        False,
        True,
        PayrollConfidentialityLevel.RESTRICTED,
        ConnectionStatus.OPERATIONAL,
        reference="synthetic-reference",
        published_on=date(2026, 1, 31),
        consulted_at=NOW,
        retrieval_evidence_id="source-evidence-fixture",
    )
    evidence = SourceEvidence(
        "source-evidence-fixture",
        source.source_id,
        "in_memory",
        ConsultationStatus.SUCCEEDED,
        NOW,
        "synthetic-reference",
        access_result="metadata_available",
    )
    return source, evidence


def payroll_report(secret="synthetic-payroll-observation"):
    source, source_evidence = source_pair()
    return ExpertReport(
        "payroll-report-fixture",
        "payroll-request-fixture",
        "paie",
        findings=(secret,),
        recommendations=("synthetic-verification",),
        proposed_actions=("synthetic-manual-review",),
        sources=(source,),
        source_evidence=(source_evidence,),
        confidence_assessments=(
            PayrollConfidenceAssessment(
                "confidence-payroll-fixture",
                ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE,
                PayrollConfidenceLevel.HIGH,
                0.8,
            ),
        ),
        status=ReportStatus.COMPLETED,
    )


def test_adapter_converts_report_and_preserves_period_confidence_provenance():
    result = PayrollAdapter(payroll_report(), SUBJECT, NOW, PERIOD).adapt()
    assert len(result.evidence) == 2
    assert len(result.findings) == 1
    assert len(result.recommendations) == 2
    assert len(result.documents) == 1
    finding_evidence = result.evidence[0]
    assert finding_evidence.period == PERIOD
    assert finding_evidence.confidence.value == 0.8
    assert finding_evidence.confidence.level is ConfidenceLevel.HIGH
    assert finding_evidence.provenance.source.source_type is SourceType.INTERNAL_REFERENTIAL
    assert result.findings[0].evidence_references == (finding_evidence.evidence_id,)


def test_document_reference_mapping_is_explicit():
    document = PayrollAdapter(payroll_report(), SUBJECT, NOW).adapt().documents[0]
    assert document.document_type is DocumentType.PAYSLIP
    assert document.metadata.document_type is DocumentType.PAYSLIP
    assert document.source.reference.source_type is SourceType.INTERNAL_REFERENTIAL


def test_absent_incomplete_and_incompatible_data_produce_diagnostics_without_raise():
    report = replace(
        payroll_report(),
        findings=(),
        sources=(),
        source_evidence=(),
        recommendations=(),
        proposed_actions=(),
        confidence_assessments=(),
        status=ReportStatus.PARTIAL,
        schema_version="2.0",
    )
    result = PayrollAdapter(report, SUBJECT, NOW).adapt()
    codes = {item.code for item in result.diagnostics}
    assert codes == {
        "PAYROLL_DATA_ABSENT",
        "PAYROLL_DATA_INCOMPLETE",
        "PAYROLL_SCHEMA_INCOMPATIBLE",
    }
    assert all(not hasattr(item, "message") for item in result.diagnostics)
