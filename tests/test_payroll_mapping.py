"""Compatibility with Evidence Graph, Reasoning Engine and safe serialization."""

from datetime import datetime, timezone

from NEXUS_ADAPTERS.payroll import PayrollAdapter
from NEXUS_CORE import EntityId, EntityReference, to_json
from NEXUS_CORE.evidence_graph import EvidenceGraph, EvidenceNode, GraphNodeType

from test_payroll_adapter import NOW, SUBJECT, payroll_report


def test_evidence_is_reference_compatible_with_evidence_graph():
    result = PayrollAdapter(payroll_report(), SUBJECT, NOW).adapt()
    graph = EvidenceGraph.empty(EntityId("graph-payroll-adapter"))
    for index, evidence in enumerate(result.evidence):
        graph = graph.add_node(
            EvidenceNode(
                EntityId(f"node-payroll-{index}"),
                GraphNodeType.EVIDENCE,
                evidence.evidence_id,
                evidence.period,
            )
        )
    assert len(graph.nodes) == len(result.evidence)


def test_evidence_is_compatible_with_reasoning_fact_extraction():
    adapter = PayrollAdapter(payroll_report(), SUBJECT, NOW)
    evidence = adapter.adapt().evidence
    facts = adapter.extract(evidence)
    assert len(facts.facts) == len(evidence)
    assert tuple(item.source_evidence for item in facts.facts) == tuple(
        item.evidence_id for item in evidence
    )


def test_sensitive_payroll_values_are_redacted_by_core_serialization():
    secret = "synthetic-sensitive-payroll-value"
    result = PayrollAdapter(payroll_report(secret), SUBJECT, NOW).adapt()
    rendered = to_json(result)
    assert secret not in rendered
    assert "<redacted>" in rendered
    assert all(not hasattr(item, "actual_value") for item in result.diagnostics)


def test_stable_input_produces_stable_identifiers():
    first = PayrollAdapter(payroll_report(), SUBJECT, NOW).adapt()
    second = PayrollAdapter(payroll_report(), SUBJECT, NOW).adapt()
    assert tuple(item.evidence_id for item in first.evidence) == tuple(
        item.evidence_id for item in second.evidence
    )
    assert tuple(item.finding_id for item in first.findings) == tuple(
        item.finding_id for item in second.findings
    )
