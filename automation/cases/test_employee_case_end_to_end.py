#!/usr/bin/env python
"""End-to-end validation of the synthetic employee-case chain (LOT 5F)."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
import sys
import threading
from typing import Any, Iterator
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "apps" / "nexus-local-interface"
FIXTURE_PATH = ROOT / "automation" / "cases" / "fixtures" / "employee-cases.synthetic.json"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(APP_DIR))

import employee_case_demo as demo  # noqa: E402
import server as server_module  # noqa: E402
from automation.cases.employee_case_comparator import DIFFERENCE_CATEGORIES, EmployeeCaseComparator  # noqa: E402
from automation.cases.employee_case_pipeline import PIPELINE_STEPS, EmployeeCasePipeline, load_fixture_cases  # noqa: E402
from automation.cases.employee_case_report import EmployeeCaseReportGenerator  # noqa: E402
from automation.cases.report_exporter import ReportExporter  # noqa: E402
from automation.payroll.payroll_data_privacy_validator import scan_object  # noqa: E402


SCENARIOS = (
    "overtime-complete",
    "on-call-incomplete",
    "sickness-contradictory",
    "classification-missing-job",
    "paid-leave-complete",
)
FIXED_TIME = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)


def exporter() -> ReportExporter:
    return ReportExporter(clock=lambda: FIXED_TIME)


@contextmanager
def local_server() -> Iterator[str]:
    server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.NexusHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def get_json(url: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - localhost only.
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def test_five_scenarios_complete_the_full_data_chain() -> None:
    for scenario_id in SCENARIOS:
        payload = demo.build_demo_payload(scenario_id)
        assert payload["pipeline"]["final_status"] in {"completed", "partial"}
        assert [item["id"] for item in payload["pipeline"]["steps"]] == list(PIPELINE_STEPS)
        assert all(item["status"] in {"completed", "warning"} for item in payload["pipeline"]["steps"])
        report = payload["report"]
        assert report["report_type"] == "employee_case_analysis"
        assert report["employee_view"] and report["expert_view"]
        assert payload["employee_view"] == report["employee_view"]
        assert payload["expert_view"] == report["expert_view"]
        for export_format in ("json", "markdown", "text"):
            exported = exporter().export(report, export_format, "standard")
            assert exported["disk_write_performed"] is False
            assert exported["calculation_performed"] is False
            assert exported["metadata"]["format"] == export_format
            json.dumps(exported, ensure_ascii=False)
            privacy = scan_object(exported)
            assert privacy["blocked_count"] == 0, privacy


def test_incomplete_scenarios_keep_documentary_blocks() -> None:
    on_call = demo.build_demo_payload("on-call-incomplete")
    classification = demo.build_demo_payload("classification-missing-job")
    assert on_call["themes_blocked"] == ["on_call"]
    assert classification["themes_blocked"] == ["classification"]
    assert on_call["report"]["sections"]["documents"]["blocking"]
    assert classification["report"]["sections"]["documents"]["blocking"]


def test_sickness_scenario_preserves_contradiction_through_export() -> None:
    payload = demo.build_demo_payload("sickness-contradictory")
    assert payload["contradictions"]
    exported = exporter().export(payload["report"], "json", "expert")
    serialized = json.dumps(exported, ensure_ascii=False)
    assert "absence_period" in serialized


def test_cockpit_endpoints_load_all_scenarios_and_views() -> None:
    with local_server() as base:
        status, listing = get_json(base + "/api/employee-case/scenarios")
        assert status == 200 and [item["id"] for item in listing["scenarios"]] == list(SCENARIOS)
        for scenario_id in SCENARIOS:
            status, payload = get_json(base + f"/api/employee-case/demo?scenario={scenario_id}")
            assert status == 200 and payload["ok"] is True
            assert payload["employee_view"] and payload["expert_view"]
        status, error = get_json(base + "/api/employee-case/demo?scenario=unknown")
        assert status == 404 and error["ok"] is False and error["error"]


def test_cockpit_exposes_blocked_themes_and_contradictions() -> None:
    with local_server() as base:
        _, blocked = get_json(base + "/api/employee-case/demo?scenario=on-call-incomplete")
        _, contradictory = get_json(base + "/api/employee-case/demo?scenario=sickness-contradictory")
    assert blocked["themes_blocked"] == ["on_call"]
    assert contradictory["contradictions"]


def test_comparator_is_stable_for_identical_report() -> None:
    report = demo.build_demo_payload("overtime-complete")["report"]
    result = EmployeeCaseComparator().compare(report, deepcopy(report))
    assert tuple(result["difference_categories"]) == DIFFERENCE_CATEGORIES
    assert result["executive_summary"]["changed_dimensions"] == []


def test_comparator_before_after_is_coherent_and_immutable() -> None:
    before = demo.build_demo_payload("overtime-complete")["report"]
    after = deepcopy(before)
    after["sections"]["analyzed_situation"]["period"] = "2099-02"
    originals = deepcopy((before, after))
    result = EmployeeCaseComparator().compare(before, after)
    assert result["substantive_differences"]["period"]["category"] == "modified"
    assert (before, after) == originals


def test_comparator_complete_against_incomplete() -> None:
    complete = demo.build_demo_payload("overtime-complete")["report"]
    incomplete = demo.build_demo_payload("on-call-incomplete")["report"]
    result = EmployeeCaseComparator().compare(complete, incomplete)
    assert "themes" in result["executive_summary"]["changed_dimensions"]
    assert "documents_missing" in result["executive_summary"]["changed_dimensions"]
    assert result["employee_view"] and result["expert_view"]


def test_comparison_can_be_exported_in_all_formats() -> None:
    left = demo.build_demo_payload("paid-leave-complete")["report"]
    right = demo.build_demo_payload("classification-missing-job")["report"]
    comparison = EmployeeCaseComparator().compare(left, right)
    for export_format in ("json", "markdown", "text"):
        result = exporter().export(comparison, export_format, "expert")
        assert result["source_type"] == "comparison"
        assert result["disk_write_performed"] is False


def test_no_real_or_sensitive_data_is_produced() -> None:
    for scenario_id in SCENARIOS:
        payload = demo.build_demo_payload(scenario_id)
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        assert "privacy_probe" not in serialized
        assert "numeric_value" not in serialized and "parameter_value" not in serialized
        report = scan_object(payload)
        assert report["blocked_count"] == 0, report


def test_runtime_privacy_probe_remains_blocked() -> None:
    privacy_case = next(item for item in load_fixture_cases(FIXTURE_PATH) if item.case_id == "CASE_PRIVACY_SYN_006")
    result = EmployeeCasePipeline().run(privacy_case, [])
    assert result["final_status"] == "blocked"
    assert result["blocked_at"] == "check_confidentiality"
    assert "confidential" in result["error"].lower()


def test_chain_has_no_calculation_or_disk_write() -> None:
    payload = demo.build_demo_payload("paid-leave-complete")
    comparison = EmployeeCaseComparator().compare(payload["report"], payload["report"])
    exported = exporter().export(comparison, "text")
    assert payload["calculation_performed"] is False
    assert payload["report"]["calculation_performed"] is False
    assert comparison["calculation_performed"] is False
    assert exported["calculation_performed"] is False
    assert exported["disk_write_performed"] is False


def measure_performance(iterations: int = 20) -> dict[str, float]:
    """Return indicative average milliseconds; values are never acceptance thresholds."""
    totals = {"pipeline": 0.0, "report": 0.0, "comparator": 0.0, "export": 0.0}
    for _ in range(iterations):
        employee_case = demo._case_for_scenario("overtime-complete")
        analyses = demo.synthetic_expert_analyses(employee_case)
        started = perf_counter()
        pipeline = EmployeeCasePipeline().run(employee_case, analyses)
        totals["pipeline"] += perf_counter() - started
        pipeline["title"] = employee_case.title
        pipeline["confidentiality"] = employee_case.confidentiality.value
        started = perf_counter()
        report = EmployeeCaseReportGenerator().generate(pipeline, analyses)
        totals["report"] += perf_counter() - started
        started = perf_counter()
        comparison = EmployeeCaseComparator().compare(report, report)
        totals["comparator"] += perf_counter() - started
        started = perf_counter()
        exporter().export(comparison, "json")
        totals["export"] += perf_counter() - started
    return {name: round(total * 1000 / iterations, 3) for name, total in totals.items()}


def test_performance_measurement_covers_all_components() -> None:
    measurements = measure_performance(5)
    assert set(measurements) == {"pipeline", "report", "comparator", "export"}
    assert all(value >= 0 for value in measurements.values())


def run_all() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"LOT 5F end-to-end validation: {len(tests)} tests OK")
    print("PERFORMANCE_MS=" + json.dumps(measure_performance(), sort_keys=True))


if __name__ == "__main__":
    run_all()
