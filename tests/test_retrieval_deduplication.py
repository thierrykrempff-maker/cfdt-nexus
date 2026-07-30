from SYNDICAL_REASONING_ENGINE import build_evidence_bundles, select_evidence
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for, with_distinct_id


def test_identical_document_is_selected_only_once():
    plan = plan_for()
    bundle = build_evidence_bundles(plan, summary_for(plan))[0]
    selection = select_evidence((bundle, with_distinct_id(bundle, "duplicate")))
    assert len(selection.selected) == 1
    assert selection.rejected[0][1] == "doublon documentaire"
