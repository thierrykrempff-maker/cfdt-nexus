from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import PlanningStatus, build_case_factual_core, build_research_plan


def test_ambiguous_ten_percent_rule_creates_only_conditional_queries() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Une règle dite des 10 % était appliquée lors des congés annuels.
- Le sens de cette expression n'est pas précisé.
Informations manquantes :
- La signification exacte de la règle des 10 %.
""",
        origin_session_id="ambiguous-ten-percent",
    )
    plan = build_research_plan(core)

    assert plan.completeness_status is PlanningStatus.BLOCKED_BY_MISSING_FACTS
    assert not plan.queries
    assert plan.blocked_queries
    assert all(
        query.status is PlanningStatus.CONDITIONAL_QUERY
        for query in plan.blocked_queries
    )
    assert len({issue.issue_category for issue in plan.issues}) == 3


def test_incomplete_cssct_case_remains_suspended() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Un élu s'est vu refuser des heures destinées à une réunion CSSCT.
- Le récit disponible est incomplet.
Informations manquantes :
- La convocation et la nature exacte du temps.
""",
        origin_session_id="blocked-cssct",
    )
    plan = build_research_plan(core)

    assert plan.completeness_status is PlanningStatus.BLOCKED_BY_MISSING_FACTS
    assert not plan.queries
    assert plan.blocked_queries
