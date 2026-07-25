from __future__ import annotations

from collections import Counter
import re

from tools.run_nexus_controlled_validation import load_cases


REQUIRED_FIELDS = {
    "id",
    "question",
    "context",
    "facts",
    "documents",
    "missing",
    "expected_primary",
    "expected_complementary",
    "allowed_engines",
    "expected_mode",
    "expected_urgency",
    "expected_actions",
    "forbidden_claims",
    "sensitive_elements",
    "minimum_expected",
}


def test_corpus_contains_only_complete_synthetic_cases() -> None:
    cases = load_cases()
    assert len(cases) == 34
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(REQUIRED_FIELDS <= set(case) for case in cases)
    assert all("synth" in (case["context"] + " " + " ".join(case["documents"])).casefold() or not case["documents"] for case in cases)


def test_minimum_domain_distribution_is_respected() -> None:
    counts = Counter(case["category"] for case in load_cases())
    assert counts == {
        "R1A": 3,
        "R1B": 3,
        "R1C": 4,
        "R1D": 4,
        "R1E": 4,
        "R2A": 3,
        "R2B": 3,
        "R2C": 3,
        "PAYROLL": 3,
        "TRANSVERSAL": 4,
    }


def test_negative_traps_and_failure_case_are_present() -> None:
    text = " ".join(case["question"] for case in load_cases()).casefold()
    for marker in (
        "désaccord ponctuel",
        "régularisation",
        "to_verify",
        "aucun document",
        "décision reste en attente",
    ):
        assert marker in text or marker in " ".join(
            " ".join(case["missing"]) for case in load_cases()
        ).casefold()
    assert any(case.get("failure_engine") for case in load_cases())


def test_no_real_identity_or_real_document_is_embedded() -> None:
    rendered = repr(load_cases()).casefold()
    for forbidden in ("@gmail.", "@outlook.", "iban", "nom complet :", "c:\\users\\"):
        assert forbidden not in rendered
    assert re.search(r"\bnir\b", rendered) is None
    assert "synthétique" in rendered
