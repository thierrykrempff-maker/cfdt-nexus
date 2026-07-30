from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import IssueCategory, build_case_factual_core, build_research_plan


def test_alcohol_test_plan_keeps_observed_signs_and_technical_result_distinct() -> None:
    core = build_case_factual_core(
        """
Faits allégués :
- Une haleine alcoolisée et des troubles de l'équilibre sont allégués.
- Un éthylotest positif annoncé à 0,8 g/l est allégué.
- Le contrôle aurait été réalisé avec un appareil calibré.
Informations manquantes :
- La procédure, l'unité exacte et la contre-expertise.
""",
        origin_session_id="alcohol-test-plan",
    )
    plan = build_research_plan(core)

    assert len(plan.issues) == 8
    assert {IssueCategory.ALCOHOL_TEST, IssueCategory.HEALTH_SAFETY} <= {
        issue.issue_category for issue in plan.issues
    }
    scopes = " ".join(
        text for query in plan.queries for text in query.factual_scope
    )
    assert "haleine alcoolisée" in scopes
    assert "éthylotest positif" in scopes
