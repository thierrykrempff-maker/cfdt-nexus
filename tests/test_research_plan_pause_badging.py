from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import IssueCategory, SourceFamily, build_case_factual_core, build_research_plan


def test_pause_and_badging_questions_are_distinct_and_contextual() -> None:
    core = build_case_factual_core(
        """
Faits reconnus :
- Le salarié reconnaît certaines pauses cigarette.
Faits contestés :
- Le salarié conteste le décompte global.
Faits allégués :
- La direction veut utiliser le tourniquet de sécurité du site Seveso.
""",
        origin_session_id="pause-badge-plan",
    )
    plan = build_research_plan(core)
    categories = {issue.issue_category for issue in plan.issues}

    assert len(plan.issues) == 8
    assert {IssueCategory.BREAK_TIME, IssueCategory.WORKING_TIME} <= categories
    assert {IssueCategory.EMPLOYEE_MONITORING, IssueCategory.DATA_PROTECTION} <= categories
    assert SourceFamily.CSE_MINUTES in {target.source_family for target in plan.targets}
    break_issue_ids = {
        issue.issue_id
        for issue in plan.issues
        if issue.issue_category is IssueCategory.BREAK_TIME
    }
    break_queries = [
        query for query in plan.queries
        if query.issue_id in break_issue_ids
    ]
    assert break_queries
    assert all("télétravail" in query.negative_terms for query in break_queries)
