from __future__ import annotations

import pytest

from SYNDICAL_REASONING_ENGINE import (
    AvailablePiece,
    CaseFact,
    ConfidentialityLevel,
    FactStatus,
    SourceReference,
    SyndicalCaseInput,
)


def test_input_accepts_incomplete_case_and_preserves_declared_fact():
    fact = CaseFact("Une décision est annoncée oralement.")
    case = SyndicalCaseInput("Que faire ?", declared_facts=(fact,))
    assert case.declared_facts == (fact,)
    assert case.fact_period is None


def test_fact_categories_are_strictly_separated():
    with pytest.raises(ValueError, match="declared facts"):
        SyndicalCaseInput(
            "Question",
            declared_facts=(CaseFact("Hypothèse", FactStatus.HYPOTHESIS),),
        )


def test_piece_is_metadata_only_and_immutable():
    piece = AvailablePiece(
        "piece-synthetic",
        "instruction",
        "Instruction synthétique",
        ConfidentialityLevel.INTERNAL,
    )
    assert not hasattr(piece, "content")
    with pytest.raises(AttributeError):
        piece.title = "Autre"  # type: ignore[misc]


def test_source_requires_https():
    with pytest.raises(ValueError, match="HTTPS"):
        SourceReference("s", "Titre", "other", "Autorité", "http://example.invalid")
