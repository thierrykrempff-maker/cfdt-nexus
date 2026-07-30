from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_free_shift_wording_builds_a_research_plan() -> None:
    questions = (
        "Après un départ, la direction veut obliger une salariée de jour à rejoindre une équipe postée sans consultation du CSE.",
        "Mon employeur m'impose de passer de l'équipe de jour au 3x8.",
        "Un changement d'horaire ferait passer un salarié travaillant de jour en travail posté.",
    )
    for question in questions:
        core = build_case_factual_core(question)
        plan = build_research_plan(core)
        assert core.event_category == "WORK_SCHEDULE_CHANGE"
        assert plan.issues
        assert any("contrat" in issue.title.casefold() for issue in plan.issues)


def test_poste_word_alone_does_not_trigger_shift_change() -> None:
    core = build_case_factual_core("Le poste informatique de l'accueil est en panne.")
    assert core.event_category == "GENERAL_EMPLOYEE_QUESTION"
