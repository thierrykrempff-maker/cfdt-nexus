from SYNDICAL_REASONING_ENGINE import build_case_factual_core


def test_unsuitable_ppe_is_not_presented_as_employee_misconduct() -> None:
    core = build_case_factual_core(
        "Les EPI fournis ne sont pas adaptés au risque chimique réel du poste."
    )

    assert core.event_category == "PPE_AVAILABILITY_OR_SUITABILITY"
    assert "manquement" not in core.primary_grievance_or_decision.casefold()
    assert "sans préjuger" in core.primary_grievance_or_decision.casefold()
