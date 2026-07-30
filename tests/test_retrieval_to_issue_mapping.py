from SYNDICAL_REASONING_ENGINE import build_evidence_bundles
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_retrieved_document_maps_to_exact_issue_query_and_target():
    plan = plan_for()
    bundle = build_evidence_bundles(plan, summary_for(plan))[0]
    assert (bundle.issue_id, bundle.query_id, bundle.target_id) == (
        plan.issues[0].issue_id,
        plan.queries[0].query_id,
        plan.targets[0].target_id,
    )
