from __future__ import annotations

from NEXUS_FINAL_ASSISTANT import AssistantRequest, Fact, NexusFinalAssistant


def make(question, **kwargs):
    return NexusFinalAssistant(
        {"syndical_reasoning": lambda _: {"mode": "SUCCEEDED"}}
    ).analyze(AssistantRequest(question, **kwargs))


def test_action_is_always_an_unexecuted_draft():
    action = make("Sanction disciplinaire").actions[0]
    assert action.notice == "Brouillon à relire et adapter."
    assert action.deadline is None


def test_cse_case_generates_agenda_question():
    action = make("Préparer l'ordre du jour du CSE").actions[0]
    assert action.action_type == "question_ordre_du_jour"


def test_requested_letter_is_marked_as_draft():
    action = make(
        "Contester une sanction",
        expected_output="courrier à la direction",
        facts=(Fact("Un avertissement a été remis", documented=True),),
    ).actions[0]
    assert action.action_type == "courrier_direction"
    assert action.verified_facts
    assert "relire" in action.notice.lower()


def test_critic_requires_prudence_for_unsupported_certainty():
    result = NexusFinalAssistant(
        {
            "syndical_reasoning": lambda _: {
                "mode": "SUCCEEDED",
                "analysis": {"findings": ["Harcèlement établi avec certitude"]},
            }
        }
    ).analyze(AssistantRequest("Je signale un harcèlement"))
    assert result.critic.required_corrections
    assert result.critic.publication_verdict == "BLOCKED"
