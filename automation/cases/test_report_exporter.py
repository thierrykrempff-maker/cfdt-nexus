#!/usr/bin/env python
"""Tests for the LOT 5E report export engine."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import inspect
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.cases.employee_case_comparator import EmployeeCaseComparator  # noqa: E402
from automation.cases.report_exporter import ExportFormat, ExportPrivacy, ReportExporter  # noqa: E402
from automation.cases.test_employee_case_report import generate  # noqa: E402


FIXED_TIME = datetime(2026, 7, 15, 10, 30, tzinfo=timezone.utc)


def exporter() -> ReportExporter:
    return ReportExporter(clock=lambda: FIXED_TIME)


def report() -> dict[str, object]:
    return generate()


def comparison() -> dict[str, object]:
    left = report()
    right = deepcopy(left)
    right["sections"]["analyzed_situation"]["period"] = "2099-02"
    return EmployeeCaseComparator().compare(left, right)


def test_json_export_is_structured_and_serializable() -> None:
    result = exporter().export(report(), ExportFormat.json)
    assert isinstance(result["content"], dict)
    json.dumps(result, ensure_ascii=False)


def test_markdown_export() -> None:
    result = exporter().export(report(), "markdown")
    assert isinstance(result["content"], str)
    assert "# Report Type" in result["content"]
    assert result["metadata"]["filename"].endswith(".md")


def test_plain_text_export() -> None:
    result = exporter().export(report(), "text")
    assert isinstance(result["content"], str)
    assert "Report Type:" in result["content"]
    assert result["metadata"]["filename"].endswith(".txt")


def test_simple_report_type_and_content() -> None:
    result = exporter().export(report(), "json")
    assert result["source_type"] == "report"
    assert result["content"]["report_type"] == "employee_case_analysis"


def test_comparison_export_is_distinct() -> None:
    result = exporter().export(comparison(), "json")
    assert result["source_type"] == "comparison"
    assert result["content"]["comparison_type"] == "employee_case_documentary_comparison"
    assert "comparison" in result["metadata"]["filename"]


def test_employee_export_contains_only_employee_view() -> None:
    source = report()
    result = exporter().export(source, "json", ExportPrivacy.employee)
    assert result["content"] == source["employee_view"]
    assert "expert_view" not in result["content"]
    assert "sections" not in result["content"]


def test_expert_export_contains_only_expert_view() -> None:
    source = report()
    result = exporter().export(source, "json", ExportPrivacy.expert)
    assert result["content"] == source["expert_view"]
    assert "employee_view" not in result["content"]


def test_comparison_employee_view_does_not_leak_expert_fields() -> None:
    source = comparison()
    result = exporter().export(source, "json", "employee")
    assert result["content"]["audience"] == "employee"
    assert "substantive_differences" not in result["content"]
    serialized = json.dumps(result, ensure_ascii=False)
    assert source["inputs"]["case_a"]["case_id"] not in serialized
    assert result["metadata"]["case_identifier"] == "COMPARISON"


def test_fingerprint_matches_effective_content() -> None:
    first = exporter().export(report(), "json", "employee")
    second = exporter().export(report(), "json", "employee")
    assert len(first["metadata"]["logical_fingerprint"]) == 64
    assert first["metadata"]["logical_fingerprint"] == second["metadata"]["logical_fingerprint"]


def test_fingerprint_changes_with_content_or_format() -> None:
    source = report()
    json_export = exporter().export(source, "json")
    markdown_export = exporter().export(source, "markdown")
    assert json_export["metadata"]["logical_fingerprint"] != markdown_export["metadata"]["logical_fingerprint"]


def test_filename_is_stable_and_versioned() -> None:
    first = exporter().export(report(), "markdown")
    second = exporter().export(report(), "markdown")
    assert first["metadata"]["filename"] == second["metadata"]["filename"]
    assert first["metadata"]["filename"] == "CASE_REPORT_SYN_2026-07-15_report_v1-0.md"


def test_logical_archive_path() -> None:
    result = exporter().export(report(), "json")
    assert result["metadata"]["logical_archive_path"] == "2026/CASE_REPORT_SYN/CASE_REPORT_SYN_2026-07-15_report_v1-0.json"
    assert result["metadata"]["archive_year"] == 2026


def test_no_disk_write_occurs(tmp_path: Path | None = None) -> None:
    before = set(Path.cwd().iterdir())
    result = exporter().export(report(), "text")
    after = set(Path.cwd().iterdir())
    assert before == after
    assert result["disk_write_performed"] is False
    assert result["metadata"]["automatic_disk_write"] is False


def test_input_is_immutable() -> None:
    source = comparison()
    original = deepcopy(source)
    exporter().export(source, "markdown", "expert")
    assert source == original


def test_non_synthetic_and_unknown_sources_are_rejected() -> None:
    source = report()
    source["synthetic_only"] = False
    for invalid in (source, {"synthetic_only": True}):
        try:
            exporter().export(invalid, "json")
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid sources must be rejected.")


def test_metadata_and_safety_indicators() -> None:
    result = exporter().export(report(), "json", "standard")
    metadata = result["metadata"]
    assert metadata["generated_at_utc"] == "2026-07-15T10:30:00Z"
    assert metadata["format"] == "json" and metadata["privacy"] == "standard"
    assert metadata["source_version"] == "1.0"
    assert result["calculation_performed"] is False
    assert result["expert_invocation_performed"] is False


def test_no_external_library_or_business_engine_dependency() -> None:
    from automation.cases import report_exporter as module

    source = inspect.getsource(module)
    assert "payroll_rule_engine" not in source
    assert "EmployeeCasePipeline" not in source
    assert "EmployeeCaseReportGenerator" not in source
    assert "reportlab" not in source and "pypdf" not in source
    assert "open(" not in source and "write_text" not in source and "write_bytes" not in source


def run_all() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"LOT 5E report exporter: {len(tests)} tests OK")


if __name__ == "__main__":
    run_all()
