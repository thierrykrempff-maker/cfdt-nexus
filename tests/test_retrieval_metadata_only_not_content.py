from SYNDICAL_REASONING_ENGINE import (
    EvidenceSourceType,
    RetrievalStatus,
    build_evidence_bundles,
    select_evidence,
)
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_metadata_only_catalog_is_never_projected_as_document_content():
    plan = plan_for()
    bundle = build_evidence_bundles(
        plan,
        summary_for(plan, status=RetrievalStatus.METADATA_ONLY, excerpt=None),
    )[0]
    assert bundle.source_type is EvidenceSourceType.METADATA_ONLY_CATALOG
    assert not bundle.usable_in_public_response
    assert not select_evidence((bundle,)).selected


def test_fixture_result_is_never_projected_as_real_evidence():
    plan = plan_for()
    bundle = build_evidence_bundles(
        plan,
        summary_for(plan, status=RetrievalStatus.FIXTURE_RESULT),
    )[0]
    assert not bundle.usable_in_public_response
    assert not select_evidence((bundle,)).selected
