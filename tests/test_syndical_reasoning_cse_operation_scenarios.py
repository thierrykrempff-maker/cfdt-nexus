from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import CSEOperationReasoningEngine, cse_operation_scenarios


EXPECTED = {
    "agenda_refusal",
    "apparently_late_convocation",
    "incomplete_documents",
    "documents_day_before",
    "unanswered_question",
    "oral_unrecorded_response",
    "opinion_with_reservations",
    "unable_to_opine",
    "unmet_commitment",
    "recurring_subject",
    "confidentiality_claim",
    "cse_union_confusion",
    "vote_resolution",
    "apparently_regular",
    "recurring_dysfunction",
    "extraordinary_meeting",
    "unvalidated_minutes",
    "individual_collective_context",
}


def test_all_eighteen_required_scenarios_exist():
    assert set(cse_operation_scenarios()) == EXPECTED


@pytest.mark.parametrize("scenario_code", sorted(EXPECTED))
def test_each_scenario_is_complete_deterministic_and_serializable(scenario_code):
    case = cse_operation_scenarios()[scenario_code]
    engine = CSEOperationReasoningEngine()
    first = engine.analyze(case, scenario_code=scenario_code)
    second = engine.analyze(case, scenario_code=scenario_code)
    assert first.to_dict() == second.to_dict()
    assert first.timeline
    assert first.actor_roles
    assert first.agenda_proposals
    assert first.questions
    assert first.document_requests
    assert first.deadlines
    assert first.opinion_drafts
    assert first.reservations
    assert first.resolutions
    assert len(first.strategies) == 5
    assert first.scenario_code == scenario_code


def test_cssct_expertise_and_alert_rights_remain_out_of_scope():
    rendered = str(
        CSEOperationReasoningEngine()
        .analyze(cse_operation_scenarios()["recurring_dysfunction"])
        .to_dict()
    ).lower()
    assert "expertise automatique" not in rendered
    assert "droit d'alerte déclenché" not in rendered
    assert "analyse cssct" not in rendered
