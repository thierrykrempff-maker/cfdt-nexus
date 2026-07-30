from SYNDICAL_REASONING_ENGINE import build_case_factual_core, build_research_plan


def test_obsolete_undistributed_procedure_builds_internal_targets() -> None:
    questions = (
        "L'employeur reproche à un salarié de ne pas avoir suivi une procédure chimique qui n'était plus à jour et ne lui avait pas été diffusée.",
        "La consigne de travail accessible au salarié était une ancienne version.",
        "Une instruction professionnelle a changé sans formation ni information du salarié.",
    )
    for question in questions:
        core = build_case_factual_core(question)
        plan = build_research_plan(core)
        assert core.event_category == "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE"
        assert any("procédure" in issue.title.casefold() for issue in plan.issues)
        assert any(target.mandatory for target in plan.targets)
