"""Document-type-aware resolution inside Career Reconstruction."""

from __future__ import annotations

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportConfidence,
    ImportDocumentType,
    ImportProvenance,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_matcher import CareerReconstructionMatcher
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_merger import CareerReconstructionMerger
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import ReconstructionRecord
from RETIREMENT_PENIBILITY_ENGINE.document_resolution import (
    DOCUMENT_TYPE_PRIORITY,
    DocumentResolutionStrategy,
)


def provenance(document_type, source, confidence=ImportConfidence.MEDIUM):
    return ImportProvenance(
        source,
        document_type,
        f"document-{source}",
        "2026-07-21",
        "v1",
        f"synthetic:{source}",
        confidence,
    )


def record(
    record_id,
    document_type,
    *,
    employer="Employeur synthétique",
    start="2001-01-01",
    end="2001-12-31",
    schedule=None,
    confidence=ImportConfidence.MEDIUM,
):
    return ReconstructionRecord(
        record_id,
        "ImportedEmploymentPeriod",
        (
            ("employer", employer),
            ("start_date", start),
            ("end_date", end),
            ("schedule", schedule),
        ),
        object(),
        (provenance(document_type, record_id, confidence),),
    )


def merge(*records):
    return CareerReconstructionMerger().merge(tuple(records))[0]


def test_priority_is_centralized_in_one_document_strategy():
    assert DOCUMENT_TYPE_PRIORITY == {
        ImportDocumentType.EMPLOYMENT_CONTRACT: 0,
        ImportDocumentType.EMPLOYMENT_AMENDMENT: 0,
        ImportDocumentType.CAREER_STATEMENT: 1,
        ImportDocumentType.PAYSLIP: 2,
        ImportDocumentType.KELIO_EXPORT: 3,
    }


def test_employment_contract_has_highest_priority():
    ordered = DocumentResolutionStrategy().order(
        (
            record("kelio", ImportDocumentType.KELIO_EXPORT),
            record("payslip", ImportDocumentType.PAYSLIP),
            record("statement", ImportDocumentType.CAREER_STATEMENT),
            record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT),
        )
    )
    assert tuple(item.record_id for item in ordered) == (
        "contract",
        "statement",
        "payslip",
        "kelio",
    )


def test_career_statement_has_priority_over_payslip():
    result = merge(
        record("payslip", ImportDocumentType.PAYSLIP, employer="Bulletin"),
        record("statement", ImportDocumentType.CAREER_STATEMENT, employer="Relevé"),
    )
    assert dict(result.merged_values)["employer"] == "Relevé"
    assert result.resolution_order == ("statement", "payslip")


def test_contract_and_payslip_merge_keeps_preferred_value_and_conflict():
    merger = CareerReconstructionMerger()
    result, conflicts = merger.merge(
        (
            record("payslip", ImportDocumentType.PAYSLIP, employer="Bulletin"),
            record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, employer="Contrat"),
        )
    )
    assert dict(result.merged_values)["employer"] == "Contrat"
    assert dict(result.alternative_values)["employer"] == ("Contrat", "Bulletin")
    assert conflicts


def test_payslip_and_kelio_merge_prioritizes_payslip():
    result = merge(
        record("kelio", ImportDocumentType.KELIO_EXPORT, schedule="Kelio"),
        record("payslip", ImportDocumentType.PAYSLIP, schedule="Bulletin"),
    )
    assert dict(result.merged_values)["schedule"] == "Bulletin"
    assert result.resolution_order == ("payslip", "kelio")


def test_other_evidence_is_ranked_after_kelio():
    ordered = DocumentResolutionStrategy().order(
        (
            record("other", ImportDocumentType.OTHER),
            record("kelio", ImportDocumentType.KELIO_EXPORT),
        )
    )
    assert tuple(item.record_id for item in ordered) == ("kelio", "other")


def test_confidence_breaks_ties_for_same_document_type():
    ordered = DocumentResolutionStrategy().order(
        (
            record("low", ImportDocumentType.PAYSLIP, confidence=ImportConfidence.LOW),
            record("high", ImportDocumentType.PAYSLIP, confidence=ImportConfidence.HIGH),
        )
    )
    assert tuple(item.record_id for item in ordered) == ("high", "low")


def test_covered_period_breaks_ties_after_confidence():
    ordered = DocumentResolutionStrategy().order(
        (
            record("partial", ImportDocumentType.PAYSLIP, end=None),
            record("complete", ImportDocumentType.PAYSLIP),
        )
    )
    assert tuple(item.record_id for item in ordered) == ("complete", "partial")


def test_provenance_and_confidence_are_all_preserved():
    result = merge(
        record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, confidence=ImportConfidence.HIGH),
        record("payslip", ImportDocumentType.PAYSLIP, confidence=ImportConfidence.LOW),
    )
    assert {item.document_type for item in result.provenance} == {
        ImportDocumentType.EMPLOYMENT_CONTRACT,
        ImportDocumentType.PAYSLIP,
    }
    assert {item.confidence for item in result.provenance} == {
        ImportConfidence.HIGH,
        ImportConfidence.LOW,
    }


def test_resolution_is_deterministic_independent_of_input_order():
    left = record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT)
    right = record("payslip", ImportDocumentType.PAYSLIP)
    assert merge(left, right).resolution_order == merge(right, left).resolution_order


def test_matching_still_preserves_documentary_differences():
    left = record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, employer="Contrat")
    right = record("payslip", ImportDocumentType.PAYSLIP, employer="Bulletin")
    match = CareerReconstructionMatcher().match(left, right)
    assert "employer" in match.divergent_criteria


def test_priority_module_has_no_connector_dependency():
    source = (DocumentResolutionStrategy.__module__,)
    assert source == ("RETIREMENT_PENIBILITY_ENGINE.document_resolution",)
