from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import IssueCategory, SourceFamily, build_case_factual_core, build_research_plan


def test_private_life_plan_does_not_turn_home_alcohol_into_workplace_alcohol() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Des courriels insultants ont été adressés à un collègue.
Faits reconnus :
- Le salarié reconnaît être l'auteur de courriels insultants adressés à un collègue.
Faits allégués :
- Il déclare avoir consommé de l'alcool à son domicile avant d'écrire.
""",
        origin_session_id="private-life-plan",
    )
    plan = build_research_plan(core)
    private_issue_ids = {
        issue.issue_id
        for issue in plan.issues
        if issue.issue_category is IssueCategory.PRIVATE_LIFE
    }

    assert private_issue_ids
    assert any(
        target.source_family is SourceFamily.CASE_LAW
        and target.issue_id in private_issue_ids
        for target in plan.targets
    )
    assert all(
        "alcool sur le lieu de travail" in query.negative_terms
        for query in plan.queries
        if query.issue_id in private_issue_ids
    )
