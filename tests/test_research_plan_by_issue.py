from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_each_target_and_query_belongs_to_one_identified_issue() -> None:
    core = build_case_factual_core(
        "Une salariée travaille de jour au laboratoire. La direction veut imposer un cycle posté.",
        origin_session_id="plan-links-case",
    )
    plan = build_research_plan(core)
    issue_ids = {issue.issue_id for issue in plan.issues}
    target_ids = {target.target_id for target in plan.targets}

    assert issue_ids
    assert all(target.issue_id in issue_ids and target.purpose for target in plan.targets)
    assert all(query.issue_id in issue_ids for query in plan.queries)
    assert all(query.target_id in target_ids and query.reason for query in plan.queries)
    assert all(query.factual_scope for query in plan.queries)
