from datetime import datetime, timezone

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput, ConnectorDescriptor, ConnectorDocumentSnapshot,
    ConnectorQuerySnapshot, ConnectorResponseSnapshot, ConnectorResponseStatus,
    ConnectorSourceCategory, ConnectorSourceSnapshot, GenericConnectorAdapter,
)
from NEXUS_CORE import EntityId
from NEXUS_CORE.evidence_graph import EvidenceGraph, EvidenceNode, GraphNodeType
from NEXUS_CORE.orchestration import ExecutionContext, ExecutionStatus
from NEXUS_CORE.reasoning import FactType, GenericReasoningPipeline


NOW = datetime(2026, 3, 4, tzinfo=timezone.utc)


def source(*, failed=False, document=True):
    documents = (
        (ConnectorDocumentSnapshot(
            "doc", "source", "LEGAL_TEXT", "Synthetic", content="synthetic text"
        ),) if document else ()
    )
    return ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", ()),
        ConnectorSourceSnapshot("source", "SOURCE", ConnectorSourceCategory.LEGISLATION, True),
        ConnectorQuerySnapshot("query", "QUERY"),
        ConnectorResponseSnapshot(
            "response", ConnectorResponseStatus.FAILED if failed else ConnectorResponseStatus.SUCCEEDED,
            documents, technical_errors=("SOURCE_ERROR",) if failed else (), source_confidence=0.8,
        ), NOW,
    )


def test_execute_produces_core_execution_result_without_external_call():
    result = GenericConnectorAdapter(source()).execute(ExecutionContext(
        EntityId("execution-connector"), EntityId("plan-connector"), (), (), NOW
    ))
    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.output_references


def test_evidence_is_compatible_with_graph_and_reasoning_engine():
    adapted = GenericConnectorAdapter(source()).adapt()
    evidence = adapted.evidence[0]
    graph = EvidenceGraph.empty(EntityId("graph-connector")).add_node(EvidenceNode(
        EntityId("node-connector"), GraphNodeType.EVIDENCE, evidence.evidence_id
    ))
    reasoning = GenericReasoningPipeline().reason(
        EntityId("reasoning-connector"), adapted.evidence, evidence.subject_reference,
        (FactType("connector_document"),), NOW,
    )
    assert graph.nodes
    assert reasoning.facts.facts


def test_empty_and_failed_responses_remain_structured():
    empty = GenericConnectorAdapter(source(document=False)).adapt()
    failed = GenericConnectorAdapter(source(failed=True)).execute(ExecutionContext(
        EntityId("execution-failed"), EntityId("plan-failed"), (), (), NOW
    ))
    assert empty.evidence == ()
    assert any(item.code == "CONNECTOR_RESPONSE_EMPTY" for item in empty.diagnostics)
    assert failed.status is ExecutionStatus.FAILED
