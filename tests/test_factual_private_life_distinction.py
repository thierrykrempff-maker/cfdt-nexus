from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import build_case_factual_core


def test_home_site_shift_and_message_context_alcohol_facts_remain_distinct() -> None:
    core = build_case_factual_core(
        """
Faits allégués :
- Le salarié déclare avoir consommé de l'alcool à son domicile.
- Une consommation d'alcool sur le lieu de travail est alléguée.
- Une prise de poste sous l'emprise de l'alcool est alléguée.
- L'alcool est invoqué comme contexte de messages envoyés depuis le domicile.
""",
        origin_session_id="private-life-case",
    )

    assert len(core.canonical_facts) == 4
    assert core.fact_duplicate_count == 0
    texts = [fact.canonical_text.casefold() for fact in core.canonical_facts]
    assert any("domicile" in text and "consommé" in text for text in texts)
    assert any("lieu de travail" in text for text in texts)
    assert any("prise de poste" in text for text in texts)
    assert any("contexte de messages" in text for text in texts)
