from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import SourceFamily, build_case_factual_core, build_research_plan


def test_source_priority_follows_approved_hierarchy_without_overriding_relevance() -> None:
    core = build_case_factual_core(
        "La direction veut imposer à une salariée du laboratoire un passage de jour en travail posté.",
        origin_session_id="hierarchy-case",
    )
    plan = build_research_plan(core)

    assert [target.source_priority for target in plan.targets] == sorted(
        target.source_priority for target in plan.targets
    )
    priority = {target.source_family: target.source_priority for target in plan.targets}
    assert priority[SourceFamily.INEOS_AGREEMENT] == 1
    assert priority[SourceFamily.EMPLOYMENT_CONTRACT] == 2
    assert priority[SourceFamily.CCNIC_IDCC_44] == 3
    assert priority[SourceFamily.CASE_LAW] == 5
    assert SourceFamily.OFFICIAL_GUIDANCE not in {
        target.source_family for target in plan.targets
    }
