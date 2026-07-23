from __future__ import annotations

import json

from NEXUS_RUNTIME_INTEGRATION.protection_sociale_runtime import (
    RuntimeProtectionSocialeDiagnostics,
    RuntimeProtectionSocialeMode,
    RuntimeProtectionSocialeResult,
)
from NEXUS_RUNTIME_INTEGRATION.report_mapper import RuntimeProtectionSocialeReportMapper


def test_diagnostics_contain_only_authorized_fields():
    diagnostics = RuntimeProtectionSocialeDiagnostics(
        True, 7, 2, "PROTECTION_SOCIALE_NO_RESULT"
    )
    assert diagnostics.to_dict() == {
        "protection_sociale_called": True,
        "protection_sociale_runtime_ms": 7,
        "protection_sociale_elements_used": 2,
        "protection_sociale_fallback": "PROTECTION_SOCIALE_NO_RESULT",
    }


def test_fallback_preserves_exact_historical_report_and_sources():
    report = {
        "sections": [{"id": "legacy"}], "sources": ["historical"], "markdown": "unchanged"
    }
    result = RuntimeProtectionSocialeResult(
        RuntimeProtectionSocialeMode.FALLBACK,
        RuntimeProtectionSocialeDiagnostics(
            True, 4, 0, "PROTECTION_SOCIALE_UNAVAILABLE"
        ),
    )
    assert RuntimeProtectionSocialeReportMapper().map(report, result) is report


def test_success_report_has_no_path_raw_content_or_internal_identifier():
    report = {"sections": [{"id": "legacy"}], "sources": ["historical"]}
    result = RuntimeProtectionSocialeResult(
        RuntimeProtectionSocialeMode.SUCCEEDED,
        RuntimeProtectionSocialeDiagnostics(True, 3, 2),
        1, 1,
        ("Protection sociale : 1 référence documentaire rapprochée.",),
    )
    mapped = RuntimeProtectionSocialeReportMapper().map(report, result)
    serialized = json.dumps(mapped, ensure_ascii=False)
    assert mapped["sections"][0]["id"] == "legacy"
    assert mapped["sources"] == ["historical"]
    assert mapped["sections"][-1]["id"] == "protection_sociale_runtime"
    for forbidden in (
        "C:/private", "RAW_DOCUMENTS", "synthetic-document", "source_relative_path",
        "SYNTHETIC RAW CONTENT", "299019999999999", "FR7630006000011234567890189",
        "private.employee@example.test",
    ):
        assert forbidden not in serialized


def test_no_calculated_benefit_is_exposed():
    result = RuntimeProtectionSocialeResult(
        RuntimeProtectionSocialeMode.SUCCEEDED,
        RuntimeProtectionSocialeDiagnostics(True, 1, 2),
        report_items=("Les éléments sont présentés sans calcul de garantie ou de prestation.",),
    )
    serialized = json.dumps(result.to_dict(), ensure_ascii=False).lower()
    for forbidden in ("125,50", "80 %", "capital calculé", "rente estimée"):
        assert forbidden not in serialized
