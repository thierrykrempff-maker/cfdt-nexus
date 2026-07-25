from __future__ import annotations

from NEXUS_FINAL_ASSISTANT import AssistantRequest, Fact, NexusFinalAssistant


def assistant(payloads):
    return NexusFinalAssistant(
        {name: (lambda _, value=value: value) for name, value in payloads.items()}
    )


def test_synthesis_separates_facts_hypotheses_risks_actions_and_limits():
    result = assistant(
        {
            "syndical_reasoning": {
                "mode": "SUCCEEDED",
                "analysis": {
                    "findings": ["Modification contractuelle possible à vérifier"],
                    "missing_information": ["Avenant signé ?"],
                    "recommendations": ["Demander le projet écrit"],
                },
            }
        }
    ).analyze(
        AssistantRequest(
            "Mon poste change",
            facts=(Fact("Un nouveau planning a été remis", documented=True),),
        )
    )
    assert result.summary["understanding"]
    assert result.summary["qualifications"]
    assert result.summary["missing"]
    assert result.summary["action_plan"]
    assert result.summary["limits"]


def test_quick_mode_is_bounded():
    result = assistant(
        {
            "syndical_reasoning": {
                "mode": "SUCCEEDED",
                "analysis": {"findings": ["A", "B", "C", "D"]},
            }
        }
    ).analyze(AssistantRequest("Sanction", requested_detail="QUICK"))
    assert len(result.summary["qualifications"]) <= 2


def test_conflicting_certainty_is_exposed_not_hidden():
    result = assistant(
        {
            "syndical_reasoning": {
                "mode": "SUCCEEDED",
                "analysis": {"findings": ["Situation certaine"]},
            },
            "expert_paie_v2": {
                "mode": "SUCCEEDED",
                "analysis": {"findings": ["Hypothèse à vérifier"]},
            },
        }
    ).analyze(AssistantRequest("Bulletin et sanction"))
    assert result.conflicts
    assert any("prudente" in item.resolution for item in result.conflicts)


def test_sources_are_deduplicated_and_ordered():
    payload = {
        "mode": "SUCCEEDED",
        "sources": [
            {"type": "official", "title": "Code du travail"},
            {"type": "official", "title": "Code du travail"},
        ],
    }
    result = assistant({"documentary": payload}).analyze(
        AssistantRequest("Rechercher un document et une source")
    )
    assert len(result.sources) == 1


def test_questions_are_deduplicated_and_bounded():
    payload = {
        "mode": "SUCCEEDED",
        "analysis": {"missing_information": ["Quelle date ?", "Quelle date ?", "Quel document ?"]},
    }
    result = assistant({"syndical_reasoning": payload}).analyze(
        AssistantRequest("Sanction")
    )
    assert len(result.questions) == 2
    assert len([item for item in result.questions if item.priority.value == "CRITICAL"]) <= 3
