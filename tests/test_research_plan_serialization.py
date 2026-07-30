from __future__ import annotations

import json

from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_technical_and_public_projections_are_deterministic_and_serializable() -> None:
    core = build_case_factual_core(
        "La direction veut imposer un passage de jour en travail posté.",
        origin_session_id="serialization-plan",
    )
    first = build_research_plan(core)
    second = build_research_plan(core)

    assert first == second
    json.dumps(first.to_dict(), ensure_ascii=False)
    public = first.to_public_dict()
    json.dumps(public, ensure_ascii=False)
    assert public["title"] == "Ce que Nexus doit rechercher"
    assert "plan_id" not in json.dumps(public)
    assert "issue_id" not in json.dumps(public)
    assert "target_id" not in json.dumps(public)
    assert "query_id" not in json.dumps(public)
