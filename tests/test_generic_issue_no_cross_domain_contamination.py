from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_cse_rest_case_has_no_ppe_or_classification_issue() -> None:
    plan = build_research_plan(
        build_case_factual_core(
            "Une élue CSE en 5x8 participe à une réunion pendant son repos."
        )
    )
    categories = {issue.issue_category.value for issue in plan.issues}

    assert "PPE" not in categories
    assert "CLASSIFICATION" not in categories
    assert "DISCIPLINARY_GROUNDS" not in categories
