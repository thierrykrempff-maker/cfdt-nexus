from dataclasses import FrozenInstanceError, replace

import pytest

from SYNDICAL_REASONING_ENGINE import build_evidence_bundles
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_evidence_bundle_is_immutable_serializable_and_fully_linked():
    plan = plan_for()
    bundle = build_evidence_bundles(plan, summary_for(plan))[0]
    assert bundle.case_session_id == plan.case_session_id
    assert bundle.issue_id == plan.issues[0].issue_id
    assert bundle.fact_ids == plan.issues[0].associated_fact_ids
    assert bundle.query_id == plan.queries[0].query_id
    assert bundle.target_id == plan.targets[0].target_id
    assert bundle.to_dict()["retrieval_status"] == "LOCAL_DOCUMENT"
    with pytest.raises(FrozenInstanceError):
        bundle.title = "autre"  # type: ignore[misc]
    with pytest.raises(ValueError):
        replace(bundle, fact_ids=())
