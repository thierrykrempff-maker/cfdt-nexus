from __future__ import annotations

from pathlib import Path

from SYNDICAL_REASONING_ENGINE import build_case_factual_core


ROOT = Path(__file__).resolve().parents[1]


def test_two_cases_never_share_fact_identity_or_formulations() -> None:
    first = build_case_factual_core(
        "Faits reconnus :\n- Le salarié reconnaît certains mots.",
        origin_session_id="case-one",
    )
    second = build_case_factual_core(
        "Faits allégués :\n- Une fatigue importante est alléguée.",
        origin_session_id="case-two",
    )

    assert {fact.fact_id for fact in first.canonical_facts}.isdisjoint(
        fact.fact_id for fact in second.canonical_facts
    )
    assert all(
        fact.origin_session_id == "case-one" for fact in first.canonical_facts
    )
    assert all(
        fact.origin_session_id == "case-two" for fact in second.canonical_facts
    )
    assert "fatigue" not in str(first.to_dict()).casefold()
    assert "certains mots" not in str(second.to_dict()).casefold()


def test_generic_engine_contains_no_historical_case_identifier() -> None:
    sources = (
        ROOT / "SYNDICAL_REASONING_ENGINE" / "factual_core.py",
        ROOT / "SYNDICAL_REASONING_ENGINE" / "factual_models.py",
    )
    content = "\n".join(path.read_text(encoding="utf-8") for path in sources)

    assert "REAL-" not in content
