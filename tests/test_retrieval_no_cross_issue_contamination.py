from dataclasses import replace

import pytest

from SYNDICAL_REASONING_ENGINE import build_evidence_bundles
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_event_linked_to_another_issue_is_rejected():
    plan = plan_for()
    summary = summary_for(plan)
    event = replace(summary.events[0], issue_id="issue-other")
    with pytest.raises(ValueError, match="not linked"):
        build_evidence_bundles(plan, replace(summary, events=(event,)))
