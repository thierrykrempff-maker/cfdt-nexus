from __future__ import annotations

from tools.run_nexus_controlled_validation import (
    activation_recommendation,
    load_cases,
    public_matrix,
    run_campaign,
)


def test_campaign_meets_controlled_activation_thresholds() -> None:
    campaign = run_campaign(load_cases())
    assert campaign["case_count"] == 34
    assert campaign["score_average"] >= 90
    assert campaign["score_minimum"] >= 70
    assert campaign["below_80"] == []
    assert campaign["below_70"] == []
    assert campaign["unacceptable_cases"] == []
    assert activation_recommendation(campaign) == "PRÊT POUR ACTIVATION CONTRÔLÉE"


def test_campaign_has_no_privacy_or_calculation_incident() -> None:
    campaign = run_campaign(load_cases())
    assert campaign["privacy_incidents"] == 0
    assert campaign["forbidden_calculations"] == 0
    assert campaign["global_crashes"] == 0
    assert campaign["unresolved_contradictions"] == 0


def test_public_matrix_does_not_retain_assistant_payloads() -> None:
    matrix = public_matrix(run_campaign(load_cases()))
    assert all("assistant" not in row for row in matrix["results"])
    assert all("question" not in row and "context" not in row for row in matrix["results"])


def test_campaign_is_deterministic_apart_from_timestamp() -> None:
    first = public_matrix(run_campaign(load_cases()))
    second = public_matrix(run_campaign(load_cases()))
    assert first == second
