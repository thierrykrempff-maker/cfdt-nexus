from __future__ import annotations

import json
import re

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
    RuntimeSyndicalReasoningReportMapper,
    needs_syndical_reasoning,
)


ANSWER = {
    "query": "L'employeur peut-il changer mes horaires et comment réagir avec le CSE ?",
    "route": {
        "domains": ["temps_travail", "cse"],
        "intents": ["conseiller_salarie"],
    },
    "sources": [
        {
            "origin": "legifrance",
            "title": "Code du travail",
            "canonical_url": "https://www.legifrance.gouv.fr",
        }
    ],
}


def test_detection_uses_existing_route_and_question():
    assert needs_syndical_reasoning(ANSWER)
    assert not needs_syndical_reasoning({"query": "Bonjour", "route": {}})


def test_feature_flag_is_disabled_by_default():
    config = RuntimeSyndicalReasoningConfig.from_env({})
    result = RuntimeSyndicalReasoningIntegration(config).integrate(ANSWER)
    assert result.mode is RuntimeSyndicalReasoningMode.DISABLED
    assert result.report is None


def test_enabled_runtime_builds_case_and_report_with_citation():
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True),
        timer=lambda: 1.0,
    ).integrate(ANSWER)
    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.report is not None
    assert result.report.citations[0].title == "Code du travail"
    assert result.diagnostics.fallback_code is None


def test_report_mapper_preserves_legacy_report_when_disabled_or_failed():
    legacy = {"sections": [{"id": "legacy"}], "markdown": "historique"}
    disabled = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(False)
    ).integrate(ANSWER)
    assert RuntimeSyndicalReasoningReportMapper().map(legacy, disabled) is legacy


def test_report_mapper_appends_without_overwriting_historical_sections():
    legacy = {"sections": [{"id": "legacy"}], "generated_from": ["historique"]}
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True),
        timer=lambda: 1.0,
    ).integrate(ANSWER)
    mapped = RuntimeSyndicalReasoningReportMapper().map(legacy, result)
    assert [item["id"] for item in mapped["sections"]] == [
        "legacy",
        "syndical_reasoning_runtime",
    ]
    assert legacy == {"sections": [{"id": "legacy"}], "generated_from": ["historique"]}


def test_runtime_diagnostics_and_public_views_contain_no_sensitive_values(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "socket",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("network forbidden")
        ),
    )
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True),
        timer=lambda: 1.0,
    ).integrate(ANSWER)
    rendered = json.dumps(result.to_dict(), ensure_ascii=False).lower()
    assert re.search(r"\b(?:nir|iban|rib)\b", rendered) is None
    for forbidden in ("c:\\", "/users/", "/home/", "chunk_", "storage_id"):
        assert forbidden not in rendered
