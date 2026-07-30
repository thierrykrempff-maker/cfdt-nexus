from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_laboratory_scope_is_used_only_when_established_by_a_fact() -> None:
    scoped = build_research_plan(
        build_case_factual_core(
            "Une salariée du laboratoire travaille de jour et un passage posté est envisagé.",
            origin_session_id="laboratory-scope",
        )
    )
    unscoped = build_research_plan(
        build_case_factual_core(
            "Un salarié travaille de jour et un passage posté est envisagé.",
            origin_session_id="unknown-scope",
        )
    )

    assert {query.establishment_scope for query in scoped.queries} == {
        "INEOS_SARRALBE_LABORATORY"
    }
    assert {query.establishment_scope for query in unscoped.queries} == {
        "ESTABLISHMENT_NOT_ESTABLISHED"
    }
    assert all("laboratoire" not in query.query_text for query in unscoped.queries)
