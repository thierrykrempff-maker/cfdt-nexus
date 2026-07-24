from __future__ import annotations

import re

import pytest

from SYNDICAL_REASONING_ENGINE import (
    DisciplinaryQualification,
    DisciplinaryReasoningEngine,
    disciplinary_scenarios,
)


@pytest.fixture(scope="module")
def results():
    engine = DisciplinaryReasoningEngine()
    return {
        code: engine.analyze(case, scenario_code=code)
        for code, case in disciplinary_scenarios().items()
    }


def test_exactly_seven_required_scenarios_exist():
    assert set(disciplinary_scenarios()) == {
        "contested_warning",
        "disciplinary_suspension",
        "gross_misconduct_dismissal",
        "professional_insufficiency",
        "protected_employee",
        "irregular_procedure",
        "admitted_fault_disproportionate_measure",
    }


@pytest.mark.parametrize(
    ("code", "qualification"),
    (
        ("contested_warning", DisciplinaryQualification.WARNING),
        ("disciplinary_suspension", DisciplinaryQualification.DISCIPLINARY_SUSPENSION),
        ("gross_misconduct_dismissal", DisciplinaryQualification.DISMISSAL_GROSS_MISCONDUCT),
        ("professional_insufficiency", DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY),
        ("protected_employee", DisciplinaryQualification.PROTECTED_EMPLOYEE),
    ),
)
def test_scenarios_select_expected_provisional_qualification(results, code, qualification):
    assert qualification in {
        item.qualification for item in results[code].qualification_candidates
    }


def test_irregular_procedure_requests_missing_procedure_pieces(results):
    result = results["irregular_procedure"]
    assert "convocation" in " ".join(item.label.lower() for item in result.evidence)
    assert "notification" in " ".join(result.procedure_checks)


def test_admitted_fault_keeps_proportionality_open(results):
    result = results["admitted_fault_disproportionate_measure"]
    assert "proportionnée" in " ".join(
        item.question for item in result.automatic_questions
    )
    assert all(item.provisional for item in result.qualification_candidates)


def test_scenarios_are_metadata_only_and_do_not_expose_sensitive_fields(results):
    for result in results.values():
        payload = result.to_dict()
        rendered = str(payload).lower()
        for forbidden in ("fulltext", "document_content", "local_path", "nir", "iban"):
            assert re.search(rf"\b{forbidden}\b", rendered) is None
