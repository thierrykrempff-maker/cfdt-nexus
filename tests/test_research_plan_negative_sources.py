from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import SourceFamily, build_case_factual_core, build_research_plan


def test_unrelated_prevention_and_health_insurance_searches_are_excluded() -> None:
    core = build_case_factual_core(
        "Un salarié reconnaît être l'auteur de courriels insultants adressés à un collègue.",
        origin_session_id="negative-email-case",
    )
    plan = build_research_plan(core)
    reasons = " ".join(item.reason for item in plan.exclusions)

    assert "CARSAT et INRS exclues" in reasons
    assert "CPAM exclue" in reasons
    assert all("harcèlement sexuel" not in query.query_text for query in plan.queries)


def test_no_cnil_target_without_monitoring_or_personal_data_issue() -> None:
    core = build_case_factual_core(
        "Un salarié ne dispose pas des EPI adaptés pendant une opération chimique dangereuse.",
        origin_session_id="negative-ppe-case",
    )
    plan = build_research_plan(core)

    assert any("CNIL exclue" in item.reason for item in plan.exclusions)
    assert all(
        not (
            target.source_family is SourceFamily.OFFICIAL_GUIDANCE
            and "données" in target.purpose.casefold()
        )
        for target in plan.targets
    )
