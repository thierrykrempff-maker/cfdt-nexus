from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_pointed_overtime_missing_from_payroll_is_planned() -> None:
    questions = (
        "Des heures supplémentaires figurent au pointage mais ne sont pas payées sur le bulletin.",
        "Mes heures en plus apparaissent dans le pointage mais pas sur la fiche de paie.",
        "Le bulletin ne paie pas les heures supplémentaires validées par le responsable.",
    )
    for question in questions:
        core = build_case_factual_core(question)
        plan = build_research_plan(core)
        assert core.event_category == "UNPAID_OVERTIME"
        assert len(plan.issues) >= 3
        assert any("paiement" in issue.title.casefold() for issue in plan.issues)
