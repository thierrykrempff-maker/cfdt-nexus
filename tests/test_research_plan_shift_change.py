from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import IssueCategory, SourceFamily, build_case_factual_core, build_research_plan


def test_shift_change_plan_covers_contract_cycle_consequences_agreement_and_cse() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Une salariée du laboratoire travaille de jour.
- La direction veut imposer un passage posté.
- Elle est partie en pleurs.
Faits contestés :
- La salariée conteste pouvoir être contrainte sans son accord.
""",
        origin_session_id="shift-plan",
    )
    plan = build_research_plan(core)
    categories = {issue.issue_category for issue in plan.issues}
    families = {target.source_family for target in plan.targets}

    assert len(plan.issues) == 7
    assert {
        IssueCategory.CONTRACT_CHANGE,
        IssueCategory.SHIFT_CHANGE,
        IssueCategory.WORKING_TIME,
        IssueCategory.COLLECTIVE_AGREEMENT,
        IssueCategory.CSE_INFORMATION_CONSULTATION,
    } <= categories
    assert {
        SourceFamily.EMPLOYMENT_CONTRACT,
        SourceFamily.INEOS_AGREEMENT,
        SourceFamily.CSE_MINUTES,
    } <= families
