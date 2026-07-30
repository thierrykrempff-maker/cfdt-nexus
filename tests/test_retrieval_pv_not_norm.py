from SYNDICAL_REASONING_ENGINE import (
    EvidenceSourceType,
    SourceFamily,
    build_evidence_bundles,
)
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_minutes_are_explicitly_qualified_as_non_normative_context():
    plan = plan_for(SourceFamily.CSE_MINUTES)
    bundle = build_evidence_bundles(plan, summary_for(plan))[0]
    assert bundle.source_type is EvidenceSourceType.CSE_CSSCT_MINUTES
    assert "ne constitue pas une norme juridique" in bundle.legal_value
