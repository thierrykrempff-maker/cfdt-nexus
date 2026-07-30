from NEXUS_RUNTIME_INTEGRATION import evaluate_applicable_evidence
from tests.public_evidence_safety_support import (
    FakeBundle,
    applicable_source,
    selection_result,
)


def test_badging_passage_remains_and_payroll_passage_is_rejected():
    useful = FakeBundle(
        "CE 2017",
        "Les badgeuses sont implantées près des vestiaires et du tourniquet.",
    )
    weak = FakeBundle(
        "CE 2017",
        "Le logiciel de paie automatise les primes et changements de roulement.",
    )
    first = evaluate_applicable_evidence(
        selection_result(useful),
        [applicable_source(useful)],
    )
    second = evaluate_applicable_evidence(
        selection_result(weak),
        [applicable_source(weak)],
    )
    assert len(first.evidence) == 1
    assert not second.evidence
