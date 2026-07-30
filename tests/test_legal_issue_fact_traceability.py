from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import build_case_factual_core, identify_legal_issues


def test_every_issue_points_to_existing_facts_and_original_wording() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Le tourniquet est normalement utilisé pour la sécurité du site Seveso.
Faits reconnus :
- Le salarié reconnaît certaines pauses cigarette.
Faits contestés :
- Le salarié conteste le décompte global de ses pauses.
Faits allégués :
- La direction veut utiliser le badgeage pour reconstituer les pauses.
""",
        origin_session_id="trace-plan-case",
    )
    fact_ids = {fact.fact_id for fact in core.canonical_facts}

    for issue in identify_legal_issues(core):
        assert set(issue.associated_fact_ids) <= fact_ids
        assert issue.original_formulations
        assert all(text.strip() for text in issue.original_formulations)
