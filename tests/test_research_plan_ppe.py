from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import IssueCategory, SourceFamily, build_case_factual_core, build_research_plan


def test_ppe_plan_separates_wearing_availability_fit_stop_duerp_and_cssct() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Un salarié ne disposait pas d'un EPI adapté pendant une opération à risque chimique.
Faits allégués :
- La direction allègue un défaut de port de l'EPI.
Informations manquantes :
- La consigne exacte, le stock et le DUERP.
""",
        origin_session_id="ppe-plan",
    )
    plan = build_research_plan(core)

    assert len(plan.issues) == 7
    assert {IssueCategory.PPE, IssueCategory.HEALTH_SAFETY, IssueCategory.CSSCT} <= {
        issue.issue_category for issue in plan.issues
    }
    assert SourceFamily.OFFICIAL_GUIDANCE in {
        target.source_family for target in plan.targets
    }
    assert any("CNIL exclue" in exclusion.reason for exclusion in plan.exclusions)


def test_generic_disciplinary_proportionality_uses_personal_context_not_ppe_technical_queries() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Le salarié a huit ans d'ancienneté sans antécédent annoncé.
Faits allégués :
- L'employeur allègue un manquement au port des EPI.
- L'indisponibilité de l'équipement adapté est alléguée.
Informations manquantes :
- La consigne applicable et la possibilité d'interrompre l'opération.
""",
        origin_session_id="generic-ppe-proportionality",
    )
    plan = build_research_plan(core)
    issue = next(
        item
        for item in plan.issues
        if item.title == "Proportionnalité d’une éventuelle sanction"
    )
    associated = {
        fact.canonical_text
        for fact in core.canonical_facts
        if fact.fact_id in issue.associated_fact_ids
    }
    issue_targets = {
        target.target_id: target
        for target in plan.targets
        if target.issue_id == issue.issue_id
    }

    assert any("ancienneté" in text for text in associated)
    assert any("manquement" in text for text in associated)
    assert all(
        target.source_family is not SourceFamily.OFFICIAL_GUIDANCE
        for target in issue_targets.values()
    )
    assert all(
        query.target_id in issue_targets
        for query in plan.queries
        if query.issue_id == issue.issue_id
    )


def test_no_disciplinary_issue_without_an_employer_grievance() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Le salarié a huit ans d'ancienneté.
- Une consigne EPI est affichée.
- Les équipements sont disponibles.
""",
        origin_session_id="ppe-without-grievance",
    )
    plan = build_research_plan(core)

    assert all(
        issue.title != "Proportionnalité d’une éventuelle sanction"
        for issue in plan.issues
    )
