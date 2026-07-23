from datetime import date, datetime, timezone

from automation.cse_memory.document_models import DocumentRecord
from NEXUS_ADAPTERS.cse import (
    CSEAdapter, CSEAdapterInput, CSEDecisionRole, CSEDecisionSnapshot,
    CSEMeetingSnapshot, CSEVoteSnapshot,
)
from NEXUS_CORE import EntityId, EntityReference
from NEXUS_CORE.orchestration import ExecutionContext, ExecutionStatus


NOW = datetime(2026, 2, 3, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("synthetic-cse-subject"), "cse_body")


def document(status="extracted"):
    return DocumentRecord(
        "synthetic-pv-one", "synthetic/path/pv.txt", "synthetic-pv.txt", ".txt",
        120, "abcdef123456", "2026-02-01T00:00:00+00:00", "2026", "minutes",
        "synthetic", "fixture", status, None, None, "", 0,
        1, None, None, None, {}, [], "2026-02-03T00:00:00+00:00",
    )


def source(version="1.0", status="extracted"):
    meeting = CSEMeetingSnapshot(
        "meeting-one", date(2026, 2, 1), "CSE",
        ("synthetic agenda",), ("participant-alpha",),
        ("synthetic-pv-one",), ("synthetic-pv-zero",), 0.9,
    )
    decision = CSEDecisionSnapshot(
        "decision-one", "meeting-one", CSEDecisionRole.FINDING_AND_RECOMMENDATION,
        "DECISION_REVIEW", "synthetic decision", ("synthetic-pv-one",),
    )
    vote = CSEVoteSnapshot(
        "vote-one", "meeting-one", "ADOPTED", 5, 1, 0,
        "decision-one", ("synthetic-pv-one",),
    )
    return CSEAdapterInput(
        SUBJECT, NOW, (document(status),), meetings=(meeting,),
        decisions=(decision,), votes=(vote,), source_schema_version=version,
    )


def test_adapter_translates_documents_meetings_decisions_and_votes():
    result = CSEAdapter(source()).adapt()
    assert len(result.documents) == 1
    assert len(result.evidence) == 3
    assert len(result.findings) == 2
    assert len(result.recommendations) == 1
    assert result.employment_periods == ()


def test_orchestration_result_is_successful_for_supported_schema():
    context = ExecutionContext(
        EntityId("execution-cse"), EntityId("plan-cse"), (), (), NOW
    )
    result = CSEAdapter(source()).execute(context)
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output_references


def test_incomplete_document_is_non_blocking_and_diagnostic_is_neutral():
    result = CSEAdapter(source(status="extracted_with_warnings")).adapt()
    assert any(item.code == "CSE_DOCUMENT_INCOMPLETE" for item in result.diagnostics)
    assert "synthetic/path" not in repr(result.diagnostics)


def test_incompatible_version_fails_execution_without_exception():
    context = ExecutionContext(
        EntityId("execution-cse"), EntityId("plan-cse"), (), (), NOW
    )
    result = CSEAdapter(source(version="2.0")).execute(context)
    assert result.status is ExecutionStatus.FAILED
    assert any(item.code == "CSE_SCHEMA_INCOMPATIBLE" for item in result.diagnostics)
