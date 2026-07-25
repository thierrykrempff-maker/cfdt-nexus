from __future__ import annotations

import pytest

from NEXUS_FINAL_ASSISTANT import AssistantRequest, Domain, NexusFinalAssistant


_SCENARIOS = (
    ("Passage de jour vers poste avec nouveau planning", Domain.CONTRACT),
    ("Sanction après refus d'un horaire", Domain.DISCIPLINE),
    ("Harcèlement avec arrêt maladie", Domain.DISCRIMINATION),
    ("Heures supplémentaires non payées sur le bulletin", Domain.WORKING_TIME),
    ("Astreinte avec repos interrompu", Domain.WORKING_TIME),
    ("Maintien maladie et IJSS incompris", Domain.HEALTH),
    ("Réorganisation du laboratoire et consultation CSE", Domain.CSE_CONSULTATION),
    ("Documents insuffisants pour la réunion CSE", Domain.CSE_OPERATION),
    ("Alerte collective et enquête CSE", Domain.CSE_ALERTS),
    ("Discrimination syndicale collective", Domain.DISCRIMINATION),
    ("Anomalie de paie collective sur le bulletin", Domain.PAYROLL),
    ("Question simple sur mon contrat", Domain.CONTRACT),
    ("Situation ambiguë sans autre précision", Domain.TRANSVERSAL),
    ("Sanction avec moteur en échec", Domain.DISCIPLINE),
    ("Bulletin et sanction potentiellement contradictoires", Domain.DISCIPLINE),
    ("Email personne@example.org dans une demande", Domain.TRANSVERSAL),
    ("Contrat avec feature flags désactivés", Domain.CONTRACT),
    ("Préparer un courrier après une sanction", Domain.DISCIPLINE),
    ("Question CSE et projet d'avis sur une réorganisation", Domain.CSE_CONSULTATION),
    ("Dossier collectif contrat paie CSE alerte", Domain.CSE_ALERTS),
)


def _assistant():
    payload = {
        "mode": "SUCCEEDED",
        "analysis": {
            "findings": ["Hypothèse à vérifier"],
            "missing_information": ["Période exacte ?"],
        },
    }
    return NexusFinalAssistant(
        {
            "syndical_reasoning": lambda _: payload,
            "expert_paie_v2": lambda _: payload,
            "cse_memory": lambda _: payload,
            "documentary": lambda _: payload,
        }
    )


@pytest.mark.parametrize(("question", "expected"), _SCENARIOS)
def test_twenty_required_scenarios_are_deterministic(question, expected):
    first = _assistant().analyze(AssistantRequest(question))
    second = _assistant().analyze(AssistantRequest(question))
    assert first.plan.primary_domain is expected
    assert first.to_dict() == second.to_dict()
    assert len(first.trace.engines_called) <= 4
