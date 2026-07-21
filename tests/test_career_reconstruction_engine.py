"""Architecture tests for the offline Career Reconstruction Engine."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import EvidenceStatus
from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportStatus,
    ImportedCareerRecord,
    ImportedClassification,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportedNightWork,
    ImportProvenance,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_contract import (
    CAREER_RECONSTRUCTION_SAFETY_CONTRACT,
    CareerReconstructionPort,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_engine import (
    CareerReconstructionEngine,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import (
    DatePrecision,
    ReconstructionConflictType,
    ReconstructionMatchType,
    ReconstructionReportView,
    ReconstructionRequest,
    ReconstructionStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import CareerTimeline


def provenance(source="source-a", document="doc-a"):
    return ImportProvenance(
        source,
        ImportDocumentType.PAYSLIP,
        document,
        "2026-07-21",
        "v1",
        "synthetic-test",
        ImportConfidence.MEDIUM,
    )


def period(record_id, employer="Employeur A", start="2001-01-01", end="2001-12-31", source="source-a"):
    return ImportedEmploymentPeriod(record_id, employer, start, end, provenance(source, f"doc-{source}"))


def context(*records, timeline=None):
    engine = CareerReconstructionEngine()
    ctx = engine.create_reconstruction_context(
        "case-1", ReconstructionRequest("request-1", "Reconstruire les faits declares"), timeline
    )
    return engine, engine.add_import_batch(
        ctx,
        ImportBatch(
            "batch-1",
            records=tuple(records),
            status=ImportStatus.VALIDATED,
        ),
    )


def test_public_contract_is_architecture_only_and_disabled():
    assert issubclass(CareerReconstructionEngine, object)
    assert hasattr(CareerReconstructionPort, "build_reconstruction_proposal")
    assert CAREER_RECONSTRUCTION_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert CAREER_RECONSTRUCTION_SAFETY_CONTRACT.enabled is False
    assert not any(
        (
            CAREER_RECONSTRUCTION_SAFETY_CONTRACT.network_allowed,
            CAREER_RECONSTRUCTION_SAFETY_CONTRACT.file_reading_allowed,
            CAREER_RECONSTRUCTION_SAFETY_CONTRACT.automatic_validation_allowed,
            CAREER_RECONSTRUCTION_SAFETY_CONTRACT.retirement_calculation_allowed,
        )
    )


def test_context_and_batch_are_immutable():
    engine, ctx = context(period("p1"))
    empty = engine.create_reconstruction_context("empty", ReconstructionRequest("r", "q"))
    assert empty.import_batches == ()
    assert len(ctx.import_batches) == 1
    with pytest.raises(FrozenInstanceError):
        ctx.context_id = "changed"


def test_candidate_and_duplicate_match_are_deterministic():
    engine, ctx = context(period("p1"), period("p2"))
    assert len(engine.build_candidates(ctx)) == 1
    match = engine.match_records(ctx)[0]
    assert match.match_type is ReconstructionMatchType.POSSIBLE_DUPLICATE
    assert engine.match_records(ctx) == engine.match_records(ctx)


def test_complementary_records_merge_without_mutating_originals():
    left = period("p1", end=None)
    right = period("p2", end="2001-12-31", source="source-b")
    engine, ctx = context(left, right)
    merges = engine.merge_compatible_records(ctx)
    assert merges and merges[0].status is ReconstructionStatus.MERGED
    assert left.end_date is None
    assert {item.source_id for item in merges[0].provenance} == {"source-a", "source-b"}


@pytest.mark.parametrize(
    "records, expected",
    [
        ((period("p1", start="2001-01-01"), period("p2", start="2002-01-01", source="source-b")), ReconstructionConflictType.DATE_CONFLICT),
        ((ImportedClassification("c1", "A", "100", "2001-01-01", "2001-12-31", provenance()), ImportedClassification("c2", "B", "100", "2001-01-01", "2001-12-31", provenance("source-b"))), ReconstructionConflictType.CLASSIFICATION_CONFLICT),
        ((ImportedNightWork("n1", "2001-01-01", "2001-12-31", "NUIT-A", provenance()), ImportedNightWork("n2", "2001-01-01", "2001-12-31", "NUIT-B", provenance("source-b"))), ReconstructionConflictType.SCHEDULE_CONFLICT),
    ],
)
def test_conflicting_values_remain_explicit(records, expected):
    engine, ctx = context(*records)
    conflicts = engine.detect_conflicts(ctx)
    assert expected in {item.conflict_type for item in conflicts}
    assert any(item.alternative_values for item in conflicts)


def test_year_only_date_remains_imprecise_with_explicit_bounds():
    record = ImportedCareerRecord(
        "event-1", "COMPANY_ENTRY", (("start_date", "2004"), ("description", "Entree declaree")), provenance()
    )
    engine, ctx = context(record)
    event = engine.prepare_timeline_proposal(ctx)[0]
    assert event.start_date.precision is DatePrecision.YEAR_ONLY
    assert event.start_date.value == "2004"
    assert (event.start_date.earliest_possible, event.start_date.latest_possible) == ("2004-01-01", "2004-12-31")


def test_gaps_include_missing_data_and_chronology():
    engine, ctx = context(period("p1", end="2001-01-31"), period("p2", start="2001-03-01", end=None))
    kinds = {item.gap_type for item in engine.detect_gaps(ctx)}
    assert {"MISSING_END_DATE", "UNEXPLAINED_INTERRUPTION"} <= kinds


def test_proposal_never_validates_itself_and_keeps_timeline_separate():
    original = CareerTimeline("existing")
    record = ImportedCareerRecord(
        "event-1", "PROMOTION", (("start_date", "2004-03-01"), ("description", "Promotion declaree")), provenance()
    )
    engine, ctx = context(record, timeline=original)
    proposal = engine.build_reconstruction_proposal(ctx)
    assert proposal.status is ReconstructionStatus.REQUIRES_HUMAN_VALIDATION
    assert proposal.validation_requirement.completed is False
    assert proposal.human_decisions and not any(item.decided for item in proposal.human_decisions)
    assert ctx.existing_timeline is original and original.events == ()
    assert proposal.proposed_events != original.events


def test_evidence_proposal_is_unverified_and_separate():
    evidence = ImportedEvidence(
        "e1", "PAYSLIP", "VERIFIED", "opaque-ref", provenance()
    )
    engine, ctx = context(evidence)
    proposed = engine.prepare_evidence_proposal(ctx)
    assert proposed.evidence[0].status is EvidenceStatus.UNVERIFIED


def test_employee_and_expert_reports_are_safe_and_distinct():
    record = ImportedCareerRecord(
        "event-1", "PROMOTION", (("start_date", "2004"), ("description", "Promotion")), provenance()
    )
    engine, ctx = context(record)
    proposal = engine.build_reconstruction_proposal(ctx)
    employee = engine.generate_reconstruction_report(ctx, proposal, ReconstructionReportView.EMPLOYEE_VIEW)
    expert = engine.generate_reconstruction_report(ctx, proposal, ReconstructionReportView.EXPERT_VIEW)
    assert employee.imported_sources == ()
    assert expert.imported_sources == ("source-a",)
    assert "aucune donnee n'est automatiquement validee" in employee.warnings[0]


def test_no_retirement_or_c2p_result_is_produced():
    engine, ctx = context(period("p1"))
    proposal = engine.build_reconstruction_proposal(ctx)
    assert not hasattr(proposal, "retirement_date")
    assert not hasattr(proposal, "c2p_points")


def test_modules_have_no_forbidden_io_or_parsing_imports():
    package = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("career_reconstruction_*.py"))
    for forbidden in ("import requests", "import urllib", "import ssl", "HTMLParser", "ElementTree", "open(", "subprocess"):
        assert forbidden not in sources
