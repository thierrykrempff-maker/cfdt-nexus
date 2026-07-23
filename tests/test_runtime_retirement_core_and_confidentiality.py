from __future__ import annotations

import json

from NEXUS_RUNTIME_INTEGRATION.retirement_runtime import (
    RuntimeRetirementDiagnostics,
    RuntimeRetirementMode,
    RuntimeRetirementResult,
)
from NEXUS_RUNTIME_INTEGRATION.report_mapper import RuntimeRetirementReportMapper


def test_diagnostics_expose_only_the_four_authorized_fields():
    diagnostics = RuntimeRetirementDiagnostics(True, 7, 2, "RETIREMENT_NO_RESULT")
    assert diagnostics.to_dict() == {
        "retirement_called": True,
        "retirement_runtime_ms": 7,
        "retirement_elements_used": 2,
        "retirement_fallback": "RETIREMENT_NO_RESULT",
    }


def test_fallback_preserves_exact_historical_report():
    report = {"sections": [{"id": "legacy"}], "markdown": "unchanged"}
    result = RuntimeRetirementResult(
        RuntimeRetirementMode.FALLBACK,
        RuntimeRetirementDiagnostics(True, 4, 0, "RETIREMENT_RUNTIME_UNAVAILABLE"),
    )
    assert RuntimeRetirementReportMapper().map(report, result) is report


def test_success_summary_contains_no_raw_or_confidential_values():
    report = {"sections": [{"id": "legacy"}], "generated_from": []}
    result = RuntimeRetirementResult(
        RuntimeRetirementMode.SUCCEEDED,
        RuntimeRetirementDiagnostics(True, 3, 2),
        (
            "Le domaine Retraite et pénibilité a été pris en compte.",
            "Aucun calcul individuel n'a été effectué.",
        ),
    )
    mapped = RuntimeRetirementReportMapper().map(report, result)
    serialized = json.dumps(mapped, ensure_ascii=False)
    assert mapped["sections"][-1]["id"] == "retirement_runtime"
    for forbidden in (
        "C:/private", "confidential", "299019999999999",
        "FR7630006000011234567890189", "private.employee@example.test",
        "INTERNAL-EMPLOYEE-ID", "document brut",
    ):
        assert forbidden not in serialized


def test_diagnostics_never_copy_exception_or_input_content():
    serialized = json.dumps(
        RuntimeRetirementDiagnostics(
            True, 1, 0, "RETIREMENT_RUNTIME_UNAVAILABLE"
        ).to_dict(),
        ensure_ascii=False,
    )
    assert "private value" not in serialized
    assert "employee identifier" not in serialized
