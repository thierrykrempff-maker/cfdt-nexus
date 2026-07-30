from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import FactCategory, build_case_factual_core


def test_semantic_wrapper_and_communication_authorship_create_one_fact() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Lors de l'entretien, le salarié reconnaît avoir envoyé les courriels.
Faits reconnus :
- Le salarié reconnaît être l'auteur des courriels.
- Un élément défavorable est reconnu : le salarié reconnaît être l'auteur des courriels.
""",
        origin_session_id="dedupe-case",
    )

    admitted = [
        fact for fact in core.canonical_facts
        if fact.category is FactCategory.ADMITTED
    ]
    assert len(admitted) == 1
    assert admitted[0].canonical_text == (
        "Le salarié reconnaît être l’auteur des courriels."
    )
    assert len(admitted[0].original_formulations) == 3
    assert admitted[0].original_formulations[0].semantic_duplicate_of is None
    assert all(
        formulation.semantic_duplicate_of == admitted[0].fact_id
        for formulation in admitted[0].original_formulations[1:]
    )
    assert core.fact_formulation_count == 3
    assert core.fact_duplicate_count == 2


def test_nearby_admissions_are_deliberately_kept_separate() -> None:
    core = build_case_factual_core(
        """
Faits reconnus :
- Le salarié reconnaît avoir envoyé les courriels.
- Le salarié reconnaît certains mots.
- Le salarié reconnaît avoir consommé de l'alcool à son domicile.
Faits contestés :
- Le salarié conteste la diffusion.
""",
        origin_session_id="separation-case",
    )

    assert len(core.canonical_facts) == 4
    assert core.fact_duplicate_count == 0
    assert len(core.facts_admitted) == 3
    assert core.facts_disputed == ["Le salarié conteste la diffusion."]
