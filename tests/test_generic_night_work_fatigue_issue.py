from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_night_work_fatigue_builds_prevention_questions() -> None:
    questions = (
        "Le travail posté de nuit provoque une fatigue qui met la sécurité en danger.",
        "Les nuits successives et le manque de repos créent un risque d'accident au travail.",
        "L'organisation du cycle 5x8 entraîne de la fatigue et un danger pour la sécurité.",
    )
    for question in questions:
        core = build_case_factual_core(question)
        plan = build_research_plan(core)
        assert core.event_category == "NIGHT_WORK_FATIGUE"
        assert any("prévention" in issue.title.casefold() for issue in plan.issues)
