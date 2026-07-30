from NEXUS_RUNTIME_INTEGRATION import evaluate_applicable_evidence
from tests.public_evidence_safety_support import (
    FakeBundle,
    applicable_source,
    selection_result,
)


def test_final_selection_requires_relation_to_legal_issue():
    bundle = FakeBundle("PV", "Le badgeage est utilisé pour localiser les vestiaires.")
    selected = evaluate_applicable_evidence(
        selection_result(
            bundle,
            issue="La proportionnalité de la sanction est-elle établie ?",
        ),
        [applicable_source(bundle)],
    )
    assert not selected.evidence
    assert selected.rejected[0]["reason"] == "INSUFFICIENT_LEGAL_ISSUE_RELATION"
