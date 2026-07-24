from __future__ import annotations

import json
import re

from SYNDICAL_REASONING_ENGINE import (
    ConfidenceLevel,
    SyndicalReasoningEngine,
    build_reference_case,
)


def test_laboratory_shift_scenario_covers_required_questions():
    report = SyndicalReasoningEngine().analyze(build_reference_case())
    assert {
        "employment_contract",
        "working_time",
        "payroll",
        "health_safety",
        "cse_consultation",
    } <= set(report.domains)
    assert report.confidence is ConfidenceLevel.LOW
    assert len(report.action_options) >= 5
    assert "sans préjuger" in report.recommended_strategy


def test_reference_scenario_does_not_decide_legality():
    report = SyndicalReasoningEngine().analyze(build_reference_case())
    rendered = json.dumps(report.expert_view(), ensure_ascii=False).lower()
    assert "la décision est légale" not in rendered
    assert "la décision est illégale" not in rendered
    assert "qualification reste provisoire" in rendered


def test_reference_fixture_contains_no_real_personal_or_confidential_data():
    rendered = json.dumps(
        SyndicalReasoningEngine().analyze(build_reference_case()).expert_view(),
        ensure_ascii=False,
    ).lower()
    assert re.search(r"\b(?:nir|iban|rib)\b", rendered) is None
    for forbidden in ("@", "c:\\", "/users/", "/home/", "chunk_", "storage_id"):
        assert forbidden not in rendered
