from NEXUS_RUNTIME_INTEGRATION import (
    RetrievalToResponseResult,
    retain_applicable_evidence,
)
from SYNDICAL_REASONING_ENGINE import build_evidence_bundles, select_evidence
from tests.connector_execution_cases import plan_for
from tests.retrieval_propagation_support import summary_for


def test_retrieved_document_maps_to_canonical_facts_and_objective():
    plan = plan_for()
    bundle = build_evidence_bundles(plan, summary_for(plan))[0]
    assert bundle.fact_ids == ("fact-1",)
    assert bundle.research_objective == plan.targets[0].purpose
    assert bundle.relevance_justification


def test_only_source_to_facts_accepted_evidence_reaches_response():
    plan = plan_for()
    selection = select_evidence(build_evidence_bundles(plan, summary_for(plan)))
    result = RetrievalToResponseResult(True, plan, summary_for(plan), selection)
    assert not retain_applicable_evidence(result, [])
    accepted = retain_applicable_evidence(
        result,
        [
                {
                    "source_title": selection.selected[0].title,
                    "article_or_clause": selection.selected[0].reference,
                    "precise_excerpt": selection.selected[0].excerpt,
                    "citation_ready": True,
                    "rejection_reason": None,
                }
        ],
    )
    assert len(accepted) == 1
