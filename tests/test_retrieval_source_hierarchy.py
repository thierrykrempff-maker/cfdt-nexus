from dataclasses import replace

from SYNDICAL_REASONING_ENGINE import (
    EvidenceSourceType,
    build_evidence_bundles,
    select_evidence,
)
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for, with_distinct_id


def test_higher_legal_source_is_selected_before_minutes():
    plan = plan_for()
    base = build_evidence_bundles(plan, summary_for(plan))[0]
    minutes = replace(
        with_distinct_id(base, "minutes"),
        source_type=EvidenceSourceType.CSE_CSSCT_MINUTES,
        title="PV CSE",
    )
    statute = replace(
        with_distinct_id(base, "statute"),
        source_type=EvidenceSourceType.STATUTE_OR_REGULATION,
        title="Code du travail",
    )
    selected = select_evidence((minutes, statute)).selected
    assert [item.source_type for item in selected] == [
        EvidenceSourceType.STATUTE_OR_REGULATION,
        EvidenceSourceType.CSE_CSSCT_MINUTES,
    ]
