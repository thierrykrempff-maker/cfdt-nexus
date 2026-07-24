from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from SYNDICAL_REASONING_ENGINE import (
    CSEHistoryMetadata,
    CSEOperationReasoningEngine,
    CommitmentStatus,
    MeetingType,
    OperationAssessment,
    cse_operation_scenarios,
    needs_cse_operation_reasoning,
)


class SyntheticHistory:
    def search_metadata(self, query):
        return (
            CSEHistoryMetadata(
                "PV synthétique – suivi d'un engagement",
                "2024-02",
                "CSE",
                "organisation",
                "Suivi",
                True,
                True,
                "échéance fictive",
                2,
            ),
        )


def test_agenda_refusal_is_documented_not_declared_irregular():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["agenda_refusal"]
    )
    assert result.meeting.refused_items
    rendered = str(result.to_dict()).lower()
    assert "refus apparent" in rendered
    assert "ordre du jour irrégulier" not in rendered


def test_convocation_deadlines_are_never_legally_calculated():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["apparently_late_convocation"]
    )
    assert result.meeting.meeting_type is MeetingType.ORDINARY
    assert all(item.legally_calculated is False for item in result.deadlines)
    assert all("confirmer" in item.uncertainty or "vérifier" in item.uncertainty for item in result.deadlines)


def test_questions_are_typed_prioritized_and_non_redundant():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["incomplete_documents"]
    )
    questions = [item.question for item in result.questions]
    assert questions
    assert len(questions) == len(set(questions))
    assert all(item.priority >= 1 for item in result.questions)


def test_opinions_are_drafts_and_do_not_decide_for_elected_members():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["opinion_with_reservations"]
    )
    assert len(result.opinion_drafts) >= 2
    assert all("trame proposée" in item.proposed_position for item in result.opinion_drafts)


def test_reservations_and_resolution_have_follow_up():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["vote_resolution"]
    )
    assert result.reservations
    assert result.resolutions
    assert result.resolutions[0].validity_to_confirm is True
    assert result.resolutions[0].follow_up_method


def test_history_and_commitments_remain_metadata_only_and_unverified():
    result = CSEOperationReasoningEngine(history_lookup=SyntheticHistory()).analyze(
        cse_operation_scenarios()["unmet_commitment"]
    )
    assert result.history
    assert result.commitments[0].status is CommitmentStatus.TO_CONFIRM
    rendered = str(result.to_dict()).lower()
    for forbidden in ("fulltext", "chunk_id", "local_path", "storage_id", "c:\\"):
        assert forbidden not in rendered


def test_apparently_regular_case_is_recognized_without_certification():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["apparently_regular"]
    )
    assert result.operation_assessment is OperationAssessment.APPARENTLY_REGULAR
    assert "automatiquement valide" not in str(result.to_dict()).lower()


def test_recurring_dysfunction_keeps_obstruction_prudent():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["recurring_dysfunction"]
    )
    assert result.operation_assessment is OperationAssessment.POSSIBLE_OBSTRUCTION_RISK
    assert "délit d'entrave constitué" not in str(result.to_dict()).lower()


def test_roles_keep_cse_and_union_competences_distinct():
    result = CSEOperationReasoningEngine().analyze(
        cse_operation_scenarios()["cse_union_confusion"]
    )
    roles = {item.actor: item for item in result.actor_roles}
    assert "négocier dans le champ syndical" in roles["délégué syndical"].primary_actions
    assert "négocier dans le champ syndical" not in roles["élus titulaires"].primary_actions


def test_models_are_immutable():
    item = CSEHistoryMetadata("PV fictif", None, "CSE", "test")
    with pytest.raises(FrozenInstanceError):
        item.title = "autre"


@pytest.mark.parametrize(
    "question",
    (
        "Le secrétaire veut inscrire ce point à l'ordre du jour.",
        "La convocation CSE est arrivée hier.",
        "Une résolution CSE est préparée pour le vote.",
    ),
)
def test_detection_requires_real_cse_operation_context(question):
    assert needs_cse_operation_reasoning(question)


def test_plain_meeting_does_not_activate_r2b():
    assert not needs_cse_operation_reasoning("Réunion commerciale de suivi des ventes.")
