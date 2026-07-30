from SYNDICAL_REASONING_ENGINE import (
    JudilibreExecutionAdapter, RetrievalStatus, SourceExecutionCoordinator, SourceFamily,
)
from tests.connector_execution_cases import plan_for


def test_judilibre_wrapper_preserves_decision_metadata() -> None:
    adapter = JudilibreExecutionAdapter(
        transport=lambda query, context: {
            "documents": ({
                "id": "decision-1", "title": "Cour de cassation",
                "case_number": "24-10.000", "jurisdiction": "Cour de cassation",
            },),
            "network_call_executed": True,
        },
        configured=True,
    )
    result = SourceExecutionCoordinator((adapter,)).execute(
        plan_for(SourceFamily.CASE_LAW), allow_network=True
    )
    assert result.events[0].status is RetrievalStatus.LIVE_RESULT_OBTAINED
    assert result.documents[0].case_number == "24-10.000"
