from __future__ import annotations

import pytest

from NEXUS_FINAL_ASSISTANT import (
    AnalysisPlanner,
    AssistantRequest,
    Domain,
    DomainDetector,
    Fact,
    ResponseMode,
)


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Mon employeur veut modifier mon contrat et mon poste.", Domain.CONTRACT),
        ("Je conteste une sanction après un refus d'horaire.", Domain.DISCIPLINE),
        ("Mes heures supplémentaires et mon repos sont incorrects.", Domain.WORKING_TIME),
        ("Je signale un harcèlement et une discrimination syndicale.", Domain.DISCRIMINATION),
        ("Je suis en arrêt maladie avec des IJSS manquantes.", Domain.HEALTH),
        ("Le CSE est consulté sur une réorganisation.", Domain.CSE_CONSULTATION),
        ("Préparer l'ordre du jour de la réunion CSE.", Domain.CSE_OPERATION),
        ("Le CSE envisage une alerte et une expertise.", Domain.CSE_ALERTS),
        ("Une rubrique manque sur mon bulletin de paie.", Domain.PAYROLL),
    ),
)
def test_detects_primary_domain(question, expected):
    matches = DomainDetector().detect(AssistantRequest(question))
    assert matches[0].domain is expected
    assert matches[0].role == "primary"
    assert matches[0].score > 0


def test_detection_uses_existing_route_and_facts_not_only_question_keywords():
    request = AssistantRequest(
        "Que devons-nous faire ?",
        facts=(Fact("Une consultation formelle est annoncée", documented=True),),
        route_domains=("reorganisation",),
        collective_case=True,
    )
    match = DomainDetector().detect(request)[0]
    assert match.domain is Domain.CSE_CONSULTATION
    assert match.confidence.value in {"MEDIUM", "HIGH"}


def test_planner_bounds_and_deduplicates_engines():
    request = AssistantRequest(
        "Anomalie de paie collective avec heures supplémentaires et alerte CSE.",
        collective_case=True,
    )
    matches = DomainDetector().detect(request)
    plan = AnalysisPlanner(max_engines=3).plan(request, matches)
    assert len(plan.execution_order) <= 3
    assert len(plan.execution_order) == len(set(plan.execution_order))
    assert plan.primary_domain is matches[0].domain


def test_planner_respects_allowed_engines_and_records_exclusions():
    request = AssistantRequest(
        "Bulletin et heures supplémentaires",
        allowed_engines=("syndical_reasoning",),
    )
    plan = AnalysisPlanner().plan(request, DomainDetector().detect(request))
    assert "expert_paie_v2" not in plan.execution_order
    assert "expert_paie_v2" in plan.excluded_engines


def test_response_mode_can_be_forced_and_expert_role_selects_expert():
    quick = AssistantRequest("Question contrat", requested_detail="QUICK")
    assert AnalysisPlanner().plan(quick, DomainDetector().detect(quick)).response_mode is ResponseMode.QUICK
    expert = AssistantRequest("Question contrat", union_role="DS")
    assert AnalysisPlanner().plan(expert, DomainDetector().detect(expert)).response_mode is ResponseMode.EXPERT
