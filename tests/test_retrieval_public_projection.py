from SYNDICAL_REASONING_ENGINE import build_evidence_bundles, select_evidence
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_public_projection_contains_business_fields_and_no_internal_ids():
    plan = plan_for()
    selection = select_evidence(build_evidence_bundles(plan, summary_for(plan)))
    payload = selection.selected[0].to_dict(public=True)
    assert payload["title"]
    assert payload["excerpt"]
    assert payload["legal_value"]
    assert payload["organization"] == "PV CSE/CSSCT"
    assert payload["passage_nature"] == "INFORMATION"
    assert not {
        "evidence_id", "case_session_id", "issue_id", "query_id",
        "target_id", "document_id", "fact_ids", "provenance",
    } & payload.keys()
