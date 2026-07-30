from __future__ import annotations

import json

from SYNDICAL_REASONING_ENGINE import (
    FactConfidence,
    FactualSource,
    build_case_factual_core,
)


def test_canonical_fact_keeps_every_original_formulation_and_source() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Lors de l'entretien, le salarié reconnaît avoir envoyé les courriels.
Faits reconnus :
- Le salarié reconnaît être l'auteur des courriels.
""",
        origin_session_id="traceability-case",
    )
    fact = core.canonical_facts[0]

    assert fact.origin_session_id == "traceability-case"
    assert fact.confidence is FactConfidence.HIGH
    assert [item.factual_source for item in fact.original_formulations] == [
        FactualSource.USER_PROVIDED,
        FactualSource.USER_ADMITTED,
    ]
    assert [item.text for item in fact.original_formulations] == [
        "Lors de l'entretien, le salarié reconnaît avoir envoyé les courriels.",
        "Le salarié reconnaît être l'auteur des courriels.",
    ]
    json.dumps(core.to_dict(), ensure_ascii=False)


def test_missing_information_is_traced_as_input_not_as_legal_conclusion() -> None:
    core = build_case_factual_core(
        """
Informations manquantes :
- La preuve de diffusion des messages.
""",
        origin_session_id="missing-case",
    )
    fact = core.canonical_facts[0]

    assert fact.factual_source is FactualSource.USER_MISSING_INFORMATION
    assert fact.confidence is FactConfidence.LOW
    assert fact.allegation_author is None
