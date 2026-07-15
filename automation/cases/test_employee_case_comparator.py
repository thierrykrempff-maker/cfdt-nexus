#!/usr/bin/env python
"""Tests for the LOT 5D documentary employee-case comparator."""

from __future__ import annotations

from copy import deepcopy
import inspect
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.cases.employee_case_comparator import (  # noqa: E402
    DIFFERENCE_CATEGORIES,
    EmployeeCaseComparator,
)
from automation.cases.test_employee_case_report import analysis, case, generate, pipeline_result  # noqa: E402


def report(*, complete: bool = True, confidence: str = "HIGH") -> dict[str, object]:
    analyses = [analysis(confidence=confidence), analysis("juriste_travail", confidence=confidence)]
    return generate(pipeline_result(complete, analyses), analyses)


def compare(left: dict[str, object], right: dict[str, object]) -> dict[str, object]:
    return EmployeeCaseComparator().compare(left, right)


def test_two_identical_reports_are_unchanged() -> None:
    value = report()
    result = compare(value, deepcopy(value))
    assert result["executive_summary"]["changed_dimensions"] == []
    assert set(result["executive_summary"]["unchanged_dimensions"]) == set(result["substantive_differences"])


def test_two_completely_different_reports() -> None:
    left = report()
    right = report(complete=False, confidence="LOW")
    right["sections"]["header"]["status"] = "blocked"
    right["sections"]["analyzed_situation"]["period"] = "2099-02"
    right["sections"]["theme_analysis"][0]["theme"] = "on_call"
    result = compare(left, right)
    assert {"period", "status", "themes", "documents_present", "confidence"} <= set(result["executive_summary"]["changed_dimensions"])


def test_document_addition_is_new() -> None:
    left = report()
    right = deepcopy(left)
    right["sections"]["documents"]["present"].append("DOC_NEW_SYN")
    delta = compare(left, right)["substantive_differences"]["documents_present"]
    assert delta["new"] == ["DOC_NEW_SYN"]


def test_document_removal_is_removed() -> None:
    left = report()
    right = deepcopy(left)
    removed = right["sections"]["documents"]["present"].pop()
    delta = compare(left, right)["substantive_differences"]["documents_present"]
    assert delta["removed"] == [removed]


def test_confidence_evolution_is_detected() -> None:
    result = compare(report(confidence="HIGH"), report(confidence="LOW"))
    assert result["substantive_differences"]["confidence"]["category"] == "modified"
    assert "confidence_decrease" in {item["type"] for item in result["detected_contradictions"]}


def test_new_contradiction_is_classified() -> None:
    left = report()
    right = deepcopy(left)
    right["sections"]["contradictions"]["items"].append("Synthetic contradiction to verify.")
    assert compare(left, right)["substantive_differences"]["contradictions"]["new"]


def test_blocked_theme_disappears() -> None:
    left = report(complete=False, confidence="LOW")
    right = report(complete=True, confidence="HIGH")
    result = compare(left, right)
    assert result["executive_summary"]["newly_unblocked_themes"] == ["overtime"]


def test_unblocked_without_new_document_is_flagged() -> None:
    left = report()
    right = deepcopy(left)
    left["sections"]["theme_analysis"][0]["status"] = "blocked"
    assert "unblocked_without_new_document" in {item["type"] for item in compare(left, right)["detected_contradictions"]}


def test_expert_findings_incompatibility_is_flagged() -> None:
    left = report()
    right = deepcopy(left)
    right["sections"]["payroll_expert_summary"]["findings"] = ["Different synthetic observation."]
    types = {item["type"] for item in compare(left, right)["detected_contradictions"]}
    assert "incompatible_expert_findings" in types


def test_inputs_are_immutable() -> None:
    left, right = report(), report(complete=False)
    originals = deepcopy((left, right))
    compare(left, right)
    assert (left, right) == originals


def test_result_is_json_serializable() -> None:
    json.dumps(compare(report(), report()), ensure_ascii=False)


def test_employee_and_expert_views_are_distinct() -> None:
    result = compare(report(), report(complete=False))
    assert result["employee_view"]["audience"] == "employee"
    assert result["expert_view"]["audience"] == "expert"
    assert "substantive_differences" not in result["employee_view"]
    assert "substantive_differences" in result["expert_view"]


def test_categories_and_theme_structure_are_complete() -> None:
    result = compare(report(), report())
    assert tuple(result["difference_categories"]) == DIFFERENCE_CATEGORIES
    theme = result["theme_analysis"][0]
    assert {"state_a", "state_b", "difference_category", "documentary_consequences", "new_documents_to_request"} <= set(theme)


def test_raw_employee_cases_are_supported() -> None:
    first = case()
    second = deepcopy(first)
    second.period = "2099-02"
    result = EmployeeCaseComparator().compare(first, second)
    assert result["inputs"]["case_a"]["source_type"] == "case"
    assert result["substantive_differences"]["period"]["category"] == "modified"


def test_non_synthetic_input_is_rejected() -> None:
    value = report()
    value["synthetic_only"] = False
    try:
        compare(value, report())
    except ValueError as error:
        assert "synthetic_only" in str(error)
    else:
        raise AssertionError("A non-synthetic input must be rejected.")


def test_comparator_never_calculates_or_invokes_experts() -> None:
    from automation.cases import employee_case_comparator as module

    source = inspect.getsource(module)
    assert "payroll_rule_engine" not in source
    assert "EmployeeCasePipeline" not in source
    assert "EmployeeCaseReportGenerator" not in source
    result = compare(report(), report())
    assert result["calculation_performed"] is False
    assert result["expert_invocation_performed"] is False


def run_all() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"LOT 5D employee case comparator: {len(tests)} tests OK")


if __name__ == "__main__":
    run_all()
