from dataclasses import replace

import pytest

from SYNDICAL_REASONING_ENGINE import build_evidence_bundles
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_summary_from_another_case_is_rejected():
    plan = plan_for(case_session_id="case-a")
    summary = replace(summary_for(plan), case_session_id="case-b")
    with pytest.raises(ValueError, match="does not belong"):
        build_evidence_bundles(plan, summary)
