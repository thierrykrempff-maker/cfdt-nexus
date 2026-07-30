from NEXUS_RUNTIME_INTEGRATION import evaluate_applicable_evidence
from tests.public_evidence_safety_support import (
    FakeBundle,
    applicable_source,
    selection_result,
)


def test_payroll_and_shift_passage_is_not_evidence_about_badging():
    bundle = FakeBundle(
        "CE 2017",
        "Le règlementaire de paie contient les motifs d’absence, les cycles, "
        "les changements de roulement et les primes de rappel.",
    )
    selected = evaluate_applicable_evidence(
        selection_result(bundle),
        [applicable_source(bundle)],
    )
    assert not selected.evidence
    assert selected.rejected[0]["reason"] in {
        "INSUFFICIENT_FINAL_FACTUAL_RELATION",
        "INSUFFICIENT_LEGAL_ISSUE_RELATION",
        "DISTINCTIVE_CONCEPT_MISSING",
    }
