from __future__ import annotations

from pathlib import Path

from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


ROOT = Path(__file__).resolve().parents[1]


def test_two_sessions_never_share_plan_issue_target_or_query_ids() -> None:
    query = (
        "Des courriels insultants ont été adressés à un collègue. "
        "Le salarié reconnaît être l'auteur des courriels."
    )
    first = build_research_plan(build_case_factual_core(query, origin_session_id="plan-one"))
    second = build_research_plan(build_case_factual_core(query, origin_session_id="plan-two"))

    id_fields = {
        "issues": "issue_id",
        "targets": "target_id",
        "queries": "query_id",
    }
    for attribute, id_field in id_fields.items():
        first_ids = {
            getattr(item, id_field)
            for item in getattr(first, attribute)
        }
        second_ids = {
            getattr(item, id_field)
            for item in getattr(second, attribute)
        }
        assert first_ids and second_ids
        assert first_ids.isdisjoint(second_ids)


def test_generic_planning_engine_contains_no_historical_case_identifier_or_network() -> None:
    paths = (
        ROOT / "SYNDICAL_REASONING_ENGINE" / "legal_issue_models.py",
        ROOT / "SYNDICAL_REASONING_ENGINE" / "research_plan.py",
    )
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    assert "REAL-" not in content
    assert "requests" not in content
    assert "urllib" not in content
    assert "http://" not in content
    assert "https://" not in content
