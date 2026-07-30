from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_cse_meeting_on_rest_day_has_time_and_cse_issues() -> None:
    questions = (
        "Un élu en 5x8 est convoqué à une réunion CSE pendant son repos et demande comment ce temps doit être payé.",
        "Une réunion du CSE est organisée hors horaire pendant le jour de repos d'un représentant.",
        "Le temps de réunion d'un élu CSE posté tombe sur son repos hebdomadaire.",
    )
    for question in questions:
        core = build_case_factual_core(question)
        plan = build_research_plan(core)
        assert core.event_category == "CSE_MEETING_REST_TIME"
        assert len(plan.issues) >= 3
        assert all("discipl" not in issue.title.casefold() for issue in plan.issues)
