"""Synthetic architecture tests for the offline Kelio Connector."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportedFiveShift,
    ImportedNightWork,
)
from RETIREMENT_PENIBILITY_ENGINE.kelio_connector import KelioConnector
from RETIREMENT_PENIBILITY_ENGINE.kelio_contract import KELIO_SAFETY_CONTRACT, KelioPort
from RETIREMENT_PENIBILITY_ENGINE.kelio_models import (
    KelioConfidence,
    KelioCounter,
    KelioEmployee,
    KelioEvidence,
    KelioExport,
    KelioFiveShift,
    KelioIntervention,
    KelioLeave,
    KelioMetadata,
    KelioNightWork,
    KelioOnCall,
    KelioReportView,
    KelioSchedule,
    KelioShift,
    KelioStatus,
    KelioWorkingDay,
    KelioWorkingTime,
)


def kelio_export():
    return KelioExport(
        KelioMetadata("export-1", "opaque-export-reference", "2026-07-21", "v1", KelioConfidence.MEDIUM),
        KelioEmployee("synthetic-employee-1"),
        schedules=(KelioSchedule("schedule-1", "Horaire synthetique", "2026-01-01"),),
        working_days=(KelioWorkingDay("day-1", "2026-01-01", "schedule-1"),),
        shifts=(KelioShift("shift-1", "day-1", "2026-01-01T22:00:00", "2026-01-02T06:00:00"),),
        night_work=(KelioNightWork("night-1", "shift-1", "8.00"),),
        five_shift=(KelioFiveShift("five-1", "schedule-1", "2026-01-01", "2026-01-31"),),
        on_calls=(KelioOnCall("on-call-1", "2026-01-03T08:00:00", "2026-01-03T18:00:00"),),
        interventions=(KelioIntervention("intervention-1", "on-call-1", "2026-01-03T10:00:00", "2026-01-03T11:00:00"),),
        leaves=(KelioLeave("leave-1", "CONGE-SYNTHETIQUE", "2026-01-10", "2026-01-11"),),
        working_times=(KelioWorkingTime("working-1", "2026-01-01", "2026-01-31", "151.67"),),
        counters=(KelioCounter("counter-1", "Compteur synthetique", "10.00", "2026-01-31"),),
        evidence=(KelioEvidence("evidence-1", "KELIO_EXPORT", "opaque-evidence-reference"),),
    )


def test_create_empty_export_is_anonymous_and_synthetic():
    empty = KelioConnector().create_empty_export("empty-1")
    assert empty.status is KelioStatus.EMPTY
    assert empty.metadata.synthetic_only is True
    assert empty.employee.anonymized is True
    assert empty.working_days == ()


def test_public_contract_is_disabled_and_declares_all_compatibilities():
    assert hasattr(KelioPort, "extract_working_time")
    assert KELIO_SAFETY_CONTRACT.status == "ARCHITECTURE_ONLY"
    assert KELIO_SAFETY_CONTRACT.enabled is False
    assert not any(
        (
            KELIO_SAFETY_CONTRACT.network_allowed,
            KELIO_SAFETY_CONTRACT.file_reading_allowed,
            KELIO_SAFETY_CONTRACT.export_parsing_allowed,
            KELIO_SAFETY_CONTRACT.ocr_allowed,
            KELIO_SAFETY_CONTRACT.api_allowed,
            KELIO_SAFETY_CONTRACT.kelio_access_allowed,
            KELIO_SAFETY_CONTRACT.real_exports_allowed,
        )
    )
    assert all(
        (
            KELIO_SAFETY_CONTRACT.career_statement_compatible,
            KELIO_SAFETY_CONTRACT.payslip_compatible,
            KELIO_SAFETY_CONTRACT.employment_contract_compatible,
            KELIO_SAFETY_CONTRACT.career_import_compatible,
            KELIO_SAFETY_CONTRACT.career_reconstruction_compatible,
            KELIO_SAFETY_CONTRACT.career_timeline_compatible,
            KELIO_SAFETY_CONTRACT.career_evidence_compatible,
            KELIO_SAFETY_CONTRACT.potential_rights_compatible,
            KELIO_SAFETY_CONTRACT.kelio_referential_compatible,
        )
    )


def test_complete_synthetic_export_is_structurally_valid():
    result = KelioConnector().validate_export(kelio_export())
    assert result.valid is True
    assert result.status is KelioStatus.VALID


@pytest.mark.parametrize(
    "changed, issue_type",
    [
        (lambda item: replace(item, working_days=(replace(item.working_days[0], date="invalid"),)), "INVALID_DATE"),
        (lambda item: replace(item, working_days=(replace(item.working_days[0], schedule_id="missing"),)), "UNKNOWN_SCHEDULE"),
        (lambda item: replace(item, shifts=item.shifts + (KelioShift("shift-2", "day-1", "2026-01-01T23:00:00", "2026-01-02T05:00:00"),)), "OVERLAPPING_SHIFT"),
        (lambda item: replace(item, night_work=(replace(item.night_work[0], shift_id="missing"),)), "UNKNOWN_SHIFT"),
        (lambda item: replace(item, night_work=(replace(item.night_work[0], declared_duration="-1"),)), "INVALID_NIGHT_WORK"),
        (lambda item: replace(item, five_shift=(replace(item.five_shift[0], schedule_id="missing"),)), "UNKNOWN_SCHEDULE"),
        (lambda item: replace(item, on_calls=(replace(item.on_calls[0], end_at="2026-01-03T07:00:00"),)), "INVALID_ON_CALL"),
        (lambda item: replace(item, interventions=(replace(item.interventions[0], start_at="2026-01-03T19:00:00", end_at="2026-01-03T20:00:00"),)), "INTERVENTION_OUTSIDE_ON_CALL"),
        (lambda item: replace(item, leaves=(replace(item.leaves[0], leave_type=None),)), "MISSING_LEAVE_TYPE"),
        (lambda item: replace(item, counters=(replace(item.counters[0], declared_value="-1"),)), "INVALID_COUNTER"),
    ],
)
def test_validation_detects_expected_structural_issues(changed, issue_type):
    result = KelioConnector().validate_export(changed(kelio_export()))
    assert result.valid is False
    assert issue_type in {item.issue_type for item in result.issues}


def test_duplicate_identifiers_are_retained_for_review():
    original = kelio_export()
    duplicate = replace(original.counters[0], label="Autre compteur")
    changed = replace(original, counters=original.counters + (duplicate,))
    result = KelioConnector().validate_export(changed)
    assert any(item.issue_type == "DUPLICATE" for item in result.issues)
    assert len(changed.counters) == 2


def test_conversion_builds_only_required_career_import_record_families():
    batch = KelioConnector().convert_to_import_batch(kelio_export())
    assert {type(item) for item in batch.records} == {
        ImportedEmploymentPeriod,
        ImportedNightWork,
        ImportedFiveShift,
        ImportedEvidence,
    }
    assert batch.synthetic_only is True


def test_conversion_preserves_night_five_shift_provenance_and_immutability():
    original = kelio_export()
    batch = KelioConnector().convert_to_import_batch(original)
    assert all(item.provenance.internal_document_id == "opaque-export-reference" for item in batch.records)
    assert next(item for item in batch.records if isinstance(item, ImportedNightWork)).schedule == "Horaire synthetique"
    assert next(item for item in batch.records if isinstance(item, ImportedFiveShift)).schedule == "Horaire synthetique"
    with pytest.raises(FrozenInstanceError):
        original.metadata.version = "v2"


def test_extract_working_time_covers_all_declared_families():
    info = KelioConnector().extract_working_time(kelio_export())
    assert info.working_period_ids == ("working-1",)
    assert info.night_work_ids == ("night-1",)
    assert info.five_shift_ids == ("five-1",)
    assert info.on_call_ids == ("on-call-1",)
    assert info.intervention_ids == ("intervention-1",)
    assert info.counters == ("Compteur synthetique:10.00",)


def test_real_export_fails_closed_before_conversion():
    original = kelio_export()
    invalid = replace(original, metadata=replace(original.metadata, synthetic_only=False))
    with pytest.raises(ValueError):
        KelioConnector().convert_to_import_batch(invalid)


def test_employee_and_expert_reports_are_distinct():
    connector = KelioConnector()
    employee = connector.generate_import_report(kelio_export(), KelioReportView.EMPLOYEE_VIEW)
    expert = connector.generate_import_report(kelio_export(), KelioReportView.EXPERT_VIEW)
    assert employee.recognized_periods == ("working-1",)
    assert employee.detected_night_work == ("night-1",)
    assert employee.provenance == ()
    assert expert.provenance == ("opaque-export-reference",)
    assert expert.counters == ("Compteur synthetique:10.00",)
    assert expert.career_import_preparation


def test_prepare_reconstruction_remains_a_human_validated_proposal():
    prepared = KelioConnector().prepare_reconstruction(kelio_export())
    assert prepared.reconstruction_proposal is not None
    assert prepared.reconstruction_proposal.validation_requirement.completed is False
    assert prepared.import_batch.synthetic_only is True


def test_connector_sources_have_no_network_pdf_ocr_api_or_export_reader():
    package = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("kelio_*.py"))
    forbidden = (
        "import requests", "import urllib", "import http", "import ssl", "socket",
        "HTMLParser", "ElementTree", "pdfplumber", "pypdf", "pytesseract", "open(",
    )
    assert not any(marker in sources for marker in forbidden)
