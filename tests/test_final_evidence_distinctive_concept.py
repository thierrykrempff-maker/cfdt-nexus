from NEXUS_RUNTIME_INTEGRATION import evaluate_applicable_evidence
from tests.public_evidence_safety_support import (
    FakeBundle,
    applicable_source,
    selection_result,
)


def test_isolated_generic_word_does_not_establish_distinctive_relation():
    bundle = FakeBundle("PV", "La direction utilise une nouvelle organisation.")
    selected = evaluate_applicable_evidence(
        selection_result(bundle),
        [applicable_source(bundle)],
    )
    assert not selected.evidence
    assert selected.rejected
