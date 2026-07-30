from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_missing_details_produce_questions_without_definitive_conclusion() -> None:
    core = build_case_factual_core(
        "Je conteste ma classification car mes tâches réelles semblent différentes."
    )
    plan = build_research_plan(core)

    assert plan.issues
    assert all(issue.legal_question.endswith("?") for issue in plan.issues)
    assert all("doit être reclassé" not in issue.legal_question.casefold() for issue in plan.issues)
