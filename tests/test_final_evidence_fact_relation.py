from NEXUS_RUNTIME_INTEGRATION import evaluate_applicable_evidence
from tests.public_evidence_safety_support import (
    FakeBundle,
    applicable_source,
    selection_result,
)


def test_final_selection_requires_relation_to_factual_scope():
    bundle = FakeBundle("PV", "Une réunion générale est programmée.")
    selected = evaluate_applicable_evidence(
        selection_result(bundle),
        [applicable_source(bundle)],
    )
    assert not selected.evidence
    assert selected.rejected[0]["reason"] == "INSUFFICIENT_FINAL_FACTUAL_RELATION"
