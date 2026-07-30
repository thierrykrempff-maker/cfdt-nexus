from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_classification_is_compared_to_actual_duties() -> None:
    questions = (
        "Ma classification ne correspond plus aux tâches réellement effectuées ni à mes responsabilités.",
        "Mon coefficient ne reflète pas les fonctions réellement exercées ni mon autonomie.",
        "Le niveau attribué est inférieur à la technicité et aux missions exercées.",
    )
    for question in questions:
        core = build_case_factual_core(question)
        plan = build_research_plan(core)
        assert core.event_category == "CLASSIFICATION_ACTUAL_DUTIES"
        assert any("fonctions" in issue.title.casefold() for issue in plan.issues)
