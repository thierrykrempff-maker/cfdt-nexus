from datetime import datetime, timezone

from automation.contracts import ExpertReport, ReportStatus
from RETIREMENT_PENIBILITY_ENGINE.retirement_models import (
    EvidenceGrade, EvidenceItem, MissingInformation, RetirementConfidence,
    RetirementOutputLevel, RetirementReport,
)
from NEXUS_ADAPTERS.retirement import RetirementAdapter, RetirementAdapterInput
from NEXUS_CORE import (
    AnalysisId, AnalysisQuestion, AnalysisRequest, AnalysisScope, CorrelationId,
    DomainSelection, EntityId, EntityReference,
)
from NEXUS_CORE.orchestration import ExecutionContext, ExecutionStatus


NOW = datetime(2026, 1, 2, tzinfo=timezone.utc)


def _report(*, missing=False):
    return RetirementReport(
        "synthetic-report", "synthetic-request", "synthetic summary",
        evidence_used=(EvidenceItem(
            "synthetic-evidence", "synthetic-source", "CAREER_STATEMENT",
            EvidenceGrade.A, verified=True, official=True,
        ),),
        missing_information=(MissingInformation(
            "missing-period", "synthetic missing period", "not supplied", True
        ),) if missing else (),
        confidence=RetirementConfidence.HIGH,
        output_level=RetirementOutputLevel.DROIT_POTENTIEL,
        recommended_actions=("request official verification",),
    )


def _adapter(*, version="1.0", missing=False):
    return RetirementAdapter(RetirementAdapterInput(
        _report(missing=missing), EntityReference(EntityId("synthetic-subject"), "person"),
        NOW, source_schema_version=version,
    ))


def _request(domain=DomainSelection.RETIREMENT_PENIBILITY):
    return AnalysisRequest(
        AnalysisId("analysis-synthetic"), CorrelationId("correlation-synthetic"),
        AnalysisQuestion("RETIREMENT_REVIEW"),
        AnalysisScope((EntityReference(EntityId("synthetic-subject"), "person"),)),
        (domain,),
    )


def test_adapter_converts_existing_retirement_outputs_without_calculation():
    result = _adapter().adapt()
    assert len(result.evidence) == 1
    assert len(result.recommendations) == 1
    assert result.employment_periods == ()
    assert result.source_schema_version == "1.0"


def test_domain_producers_filter_non_retirement_requests():
    adapter = _adapter()
    assert adapter.produce_evidence(_request(DomainSelection.PAYROLL)) == ()
    assert len(adapter.produce_evidence(_request())) == 1


def test_diagnostics_are_non_blocking_technical_codes_without_source_values():
    adapter = _adapter(missing=True)
    diagnostics = adapter.adapt().diagnostics
    rendered = repr(diagnostics)
    assert "synthetic missing period" not in rendered
    assert {item.code for item in diagnostics} == {
        "RETIREMENT_DATA_INCOMPLETE", "RETIREMENT_RECONSTRUCTION_ABSENT"
    }


def test_incompatible_schema_is_reported_to_orchestration():
    adapter = _adapter(version="2.0")
    context = ExecutionContext(
        EntityId("execution-synthetic"), EntityId("plan-synthetic"), (), (), NOW
    )
    result = adapter.execute(context)
    assert result.status is ExecutionStatus.FAILED
    assert any(item.code == "RETIREMENT_SCHEMA_INCOMPATIBLE" for item in result.diagnostics)


def test_fact_extraction_uses_public_core_reasoning_api():
    adapter = _adapter()
    facts = adapter.extract(adapter.adapt().evidence)
    assert len(facts.facts) == 1


def test_generic_expert_report_is_explicitly_translated():
    expert = ExpertReport(
        "expert-report", "expert-request", "retirement-expert",
        findings=("synthetic expert finding",),
        recommendations=("synthetic expert recommendation",),
        status=ReportStatus.COMPLETED,
    )
    source = RetirementAdapterInput(
        _report(), EntityReference(EntityId("synthetic-subject"), "person"), NOW,
        expert_report=expert,
    )
    result = RetirementAdapter(source).adapt()
    assert any(item.code == "RETIREMENT_EXPERT_FINDING" for item in result.findings)
    assert any(item.code == "RETIREMENT_EXPERT_RECOMMENDATION" for item in result.recommendations)
    assert any(item.fact_type == "retirement_expert_report" for item in result.evidence)
