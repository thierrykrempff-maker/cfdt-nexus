"""Architecture tests for the career timeline LOT 2."""

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_timeline_contract import (
    CAREER_TIMELINE_CONTRACT,
    CAREER_TIMELINE_FUTURE_SOURCES,
)
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_engine import CareerTimelineEngine
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import (
    CareerConflict,
    CareerEvent,
    CareerEventType,
    CareerEvidence,
    CareerGap,
    CareerPeriod,
    CareerTimeline,
    ClassificationHistory,
    Employer,
    EvidenceLevel,
    ExposurePeriod,
    FiveShiftPeriod,
    JobPosition,
    LeavePeriod,
    NightWorkPeriod,
    TimelineConfidence,
    TimelineReport,
    WorkSchedule,
)
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_protocol import CAREER_TIMELINE_PROTOCOL


def event(
    event_id: str,
    start: str | None = "2020-01-01",
    end: str | None = "2020-12-31",
    event_type: CareerEventType = CareerEventType.JOB_CHANGE,
    description: str = "Synthetic event",
    source: str = "synthetic_payroll",
    level: EvidenceLevel = EvidenceLevel.B,
) -> CareerEvent:
    return CareerEvent(event_id, start, end, event_type, description, source, level)


def test_contract_is_architecture_only_and_offline() -> None:
    assert CAREER_TIMELINE_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert CAREER_TIMELINE_CONTRACT.enabled is False
    assert CAREER_TIMELINE_CONTRACT.calculation_allowed is False
    assert CAREER_TIMELINE_CONTRACT.simulation_allowed is False
    assert CAREER_TIMELINE_CONTRACT.network_allowed is False
    assert CAREER_TIMELINE_CONTRACT.real_documents_allowed is False
    assert CAREER_TIMELINE_FUTURE_SOURCES == (
        "PAYROLL_ENGINE",
        "LEGAL_ENGINE",
        "CSE_ENGINE",
        "CSSCT_ENGINE",
        "RETIREMENT_ENGINE",
        "SOCIAL_PROTECTION_ENGINE",
        "AGGREGATED_SOCIAL_REPORT",
        "INEOS_AGREEMENTS",
        "IMPORTED_DOCUMENT_REFERENCES",
    )


def test_all_required_models_are_documented_and_immutable() -> None:
    models = (
        CareerTimeline, CareerEvent, CareerPeriod, Employer, JobPosition,
        ClassificationHistory, WorkSchedule, NightWorkPeriod, FiveShiftPeriod,
        ExposurePeriod, LeavePeriod, CareerGap, CareerConflict, CareerEvidence,
        TimelineReport,
    )
    assert all(model.__doc__ for model in models)
    item = event("event-1")
    with pytest.raises(FrozenInstanceError):
        item.description = "changed"


def test_event_catalog_is_complete() -> None:
    assert {item.value for item in CareerEventType} == {
        "COMPANY_ENTRY", "COMPANY_EXIT", "TRANSFER", "PROMOTION", "JOB_CHANGE",
        "COEFFICIENT_CHANGE", "CLASSIFICATION_CHANGE", "NIGHT_WORK", "FIVE_SHIFT",
        "SHIFT_WORK", "PART_TIME", "TRAINING", "ILLNESS", "WORKPLACE_ACCIDENT",
        "OCCUPATIONAL_DISEASE", "PARENTAL_LEAVE", "MILITARY_SERVICE", "UNEMPLOYMENT",
        "RETURN_TO_WORK", "END_OF_CAREER", "RETIREMENT",
    }


def test_event_contains_all_required_fields() -> None:
    assert {item.name for item in fields(CareerEvent)} == {
        "event_id", "start_date", "end_date", "event_type", "description",
        "source", "evidence_level", "comment",
    }


def test_engine_adds_and_removes_without_mutating_input() -> None:
    engine = CareerTimelineEngine()
    empty = engine.create_empty_timeline("timeline-1", "synthetic-case")
    populated = engine.add_event(empty, event("event-1"))
    removed = engine.remove_event(populated, "event-1")
    assert empty.events == ()
    assert tuple(item.event_id for item in populated.events) == ("event-1",)
    assert removed.events == ()


def test_validator_detects_dates_periods_duplicates_and_insufficient_evidence() -> None:
    engine = CareerTimelineEngine()
    timeline = CareerTimeline(
        "timeline-1",
        events=(
            event("invalid", "2020-99-01", None),
            event("impossible", "2021-02-01", "2021-01-01"),
            event("weak", level=EvidenceLevel.UNKNOWN),
            event("duplicate"),
            event("duplicate"),
        ),
    )
    issue_types = {issue.issue_type for issue in engine.validate(timeline).issues}
    assert {"INVALID_DATE", "IMPOSSIBLE_PERIOD", "INSUFFICIENT_EVIDENCE", "DUPLICATE"} <= issue_types


def test_validator_detects_overlap_and_source_conflict_without_correction() -> None:
    first = event("first", description="Version A", source="source_a")
    second = event("second", description="Version B", source="source_b")
    overlap = event("overlap", "2020-06-01", "2021-01-01", source="source_a")
    timeline = CareerTimeline("timeline-1", events=(first, second, overlap))
    result = CareerTimelineEngine().validate(timeline)
    assert {issue.issue_type for issue in result.issues} >= {"OVERLAP", "SOURCE_CONFLICT"}
    assert timeline.events == (first, second, overlap)
    assert result.conflicts[0].event_refs == ("first", "second")


def test_merge_sources_preserves_facts_and_exposes_conflicts_to_validation() -> None:
    engine = CareerTimelineEngine()
    left = CareerTimeline("left", "case", (event("left", description="A", source="payroll"),), source_ids=("payroll",))
    right = CareerTimeline("right", "case", (event("right", description="B", source="legal"),), source_ids=("legal",))
    merged = engine.merge_sources("merged", (left, right))
    assert tuple(item.event_id for item in merged.events) == ("left", "right")
    assert merged.source_ids == ("payroll", "legal")
    assert any(issue.issue_type == "SOURCE_CONFLICT" for issue in engine.validate(merged).issues)


def test_report_exposes_uncertainty_evidence_and_no_retirement_estimate() -> None:
    evidence = CareerEvidence("evidence-1", "synthetic_legal", EvidenceLevel.A, "opaque-ref")
    timeline = CareerTimeline("timeline-1", events=(event("weak", level=EvidenceLevel.UNKNOWN),), evidence=(evidence,))
    report = CareerTimelineEngine().generate_report(timeline)
    assert report.timeline is timeline
    assert report.events == timeline.events
    assert report.evidence_used == (evidence,)
    assert report.missing_evidence
    assert report.global_confidence is TimelineConfidence.UNKNOWN
    assert "retirement_date" not in {item.name for item in fields(TimelineReport)}
    assert "pension_amount" not in {item.name for item in fields(TimelineReport)}


def test_protocol_is_complete_ordered_and_declarative() -> None:
    assert tuple(step.ordinal for step in CAREER_TIMELINE_PROTOCOL) == tuple(range(1, 10))
    assert tuple(step.step_id for step in CAREER_TIMELINE_PROTOCOL) == (
        "collect", "normalize", "order", "merge", "detect_conflicts",
        "detect_gaps", "evaluate_evidence", "qualify_confidence", "generate_report",
    )
    assert "without a numeric calculation" in CAREER_TIMELINE_PROTOCOL[7].description


def test_lot_has_no_network_scraping_or_download_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    paths = tuple(root.glob("career_timeline_*.py"))
    forbidden = {
        "aiohttp", "bs4", "html.parser", "http.client", "requests", "scrapy",
        "socket", "ssl", "urllib", "urllib.request", "xml.etree.ElementTree",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert forbidden.isdisjoint(imports), path.name
