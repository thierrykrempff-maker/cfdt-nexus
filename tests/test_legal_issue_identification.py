from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import (
    IssueCategory,
    SourceFamily,
    build_case_factual_core,
    build_research_plan,
    identify_legal_issues,
)


def test_email_case_is_split_into_six_non_conclusive_issues() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Un salarié a envoyé des courriels insultants à un collègue.
Faits reconnus :
- Le salarié reconnaît être l'auteur des courriels.
Faits allégués :
- Les courriels auraient été écrits sous l'emprise de l'alcool.
Informations manquantes :
- Le contenu exact et la diffusion des courriels.
""",
        origin_session_id="email-issue-case",
    )
    issues = identify_legal_issues(core)

    assert len(issues) == 6
    assert {item.issue_category for item in issues} >= {
        IssueCategory.DISCIPLINARY_GROUNDS,
        IssueCategory.PRIVATE_LIFE,
        IssueCategory.DATA_PROTECTION,
        IssueCategory.DISCIPLINARY_PROCEDURE,
    }
    assert all(item.associated_fact_ids for item in issues)
    assert all("quels sont les droits" not in item.legal_question.casefold() for item in issues)
    assert all(not item.legal_question.casefold().startswith("le salarié a commis") for item in issues)
    plan = build_research_plan(core)
    assert SourceFamily.CSE_MINUTES in {
        target.source_family for target in plan.targets
    }
    assert all(
        exclusion.source_family is not SourceFamily.CSE_MINUTES
        for exclusion in plan.exclusions
    )
