from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import FactCategory, build_case_factual_core


def _by_text(core):
    return {fact.canonical_text: fact for fact in core.canonical_facts}


def test_recognized_alleged_disputed_and_missing_categories_remain_distinct() -> None:
    core = build_case_factual_core(
        """
Faits reconnus :
- Le salarié reconnaît certains mots.
Faits allégués :
- La direction allègue une perturbation du service.
Faits contestés :
- Le salarié conteste la diffusion.
Faits non établis :
- Les conséquences professionnelles ne sont pas établies.
Informations manquantes :
- Le contenu complet des messages.
""",
        origin_session_id="category-case",
    )
    facts = _by_text(core)

    assert facts["Le salarié reconnaît certains mots."].category is FactCategory.ADMITTED
    assert facts[
        "La direction allègue une perturbation du service."
    ].category is FactCategory.ALLEGED
    assert facts["Le salarié conteste la diffusion."].category is FactCategory.DISPUTED
    assert facts[
        "Les conséquences professionnelles ne sont pas établies."
    ].category is FactCategory.NOT_ESTABLISHED
    assert facts[
        "Le contenu complet des messages."
    ].category is FactCategory.MISSING_INFORMATION


def test_conditional_statement_is_not_promoted_to_certain_fact() -> None:
    core = build_case_factual_core(
        """
Faits fournis :
- Le poste serait listé parmi les postes soumis au contrôle.
- La prise de poste était prévue à cinq heures.
""",
        origin_session_id="conditional-case",
    )

    assert [fact.category for fact in core.canonical_facts] == [
        FactCategory.NOT_ESTABLISHED,
        FactCategory.CERTAIN,
    ]


def test_employer_argument_and_legal_question_are_not_facts() -> None:
    core = build_case_factual_core(
        """
Faits allégués :
- La direction allègue que les messages ont perturbé le service.

Argument de la direction :
- Les messages justifieraient une sanction.

Question juridique :
- Une sanction serait-elle proportionnée ?
""",
        origin_session_id="argument-case",
    )

    assert len(core.canonical_facts) == 1
    fact = core.canonical_facts[0]
    assert fact.category is FactCategory.ALLEGED
    assert fact.allegation_author == "EMPLOYER"
    assert "sanction" not in fact.canonical_text.casefold()
