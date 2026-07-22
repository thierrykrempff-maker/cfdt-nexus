from datetime import date, datetime, timezone

from automation.cse_memory.metadata_models import MetadataRecord, MetadataValue
from NEXUS_ADAPTERS.cse import (
    CSEAdapter, CSEAdapterInput, CSEDecisionMapper, CSEDecisionRole,
    CSEDecisionSnapshot, CSEMeetingMapper, CSEMeetingSnapshot, CSEVoteMapper,
    CSEVoteSnapshot,
)
from NEXUS_CORE import EntityId, EntityReference
from NEXUS_CORE.conflict_resolution import GenericConflictResolutionEngine
from NEXUS_CORE.evidence_graph import EvidenceGraph, EvidenceNode, GraphNodeType
from NEXUS_CORE.reasoning import FactType, GenericReasoningPipeline


NOW = datetime(2026, 2, 3, tzinfo=timezone.utc)
SUBJECT = EntityReference(EntityId("synthetic-cse-subject"), "cse_body")


def meeting():
    return CSEMeetingSnapshot(
        "meeting-one", date(2026, 2, 1), "CSE",
        ("agenda alpha", "agenda beta"), ("participant-alpha", "participant-beta"),
        ("pv-one",), ("pv-zero",), 0.8,
    )


def vote():
    return CSEVoteSnapshot("vote-one", "meeting-one", "ADOPTED", 4, 1, 2)


def test_meeting_preserves_date_instance_agenda_participants_documents_and_links():
    evidence = CSEMeetingMapper().map(meeting(), SUBJECT, NOW)
    fields = {item.key: item.value for item in evidence.value.fields}
    assert evidence.provenance.acquired_at.date() == date(2026, 2, 1)
    assert fields["meeting_instance"] == "CSE"
    assert fields["agenda_count"] == 2
    assert fields["participant_count"] == 2
    assert fields["document_count"] == 1
    assert fields["related_minutes_count"] == 1
    assert fields["participant_ref_0"] != "participant-alpha"


def test_decision_role_controls_translation_without_inference():
    decision = CSEDecisionSnapshot(
        "decision-one", "meeting-one", CSEDecisionRole.FINDING_AND_RECOMMENDATION,
        "FOLLOW_UP", "synthetic action",
    )
    findings, recommendations = CSEDecisionMapper().map(decision)
    assert len(findings) == 1
    assert len(recommendations) == 1


def test_vote_preserves_result_and_counts_as_evidence_and_finding():
    evidence, finding = CSEVoteMapper().map(vote(), SUBJECT, NOW)
    fields = {item.key: item.value for item in evidence.value.fields}
    assert fields == {
        "vote_result": "ADOPTED", "votes_for": 4,
        "votes_against": 1, "abstentions": 2,
    }
    assert finding.evidence_references == (evidence.evidence_id,)


def test_metadata_conflicts_become_unarbitrated_reasoning_conflicts():
    record = MetadataRecord(
        "metadata-one", "document-one", "source-one", "synthetic/path",
        "abcdef", "1.0", "1.0", "extracted", "2026-02-03T00:00:00+00:00",
        [], [{"kind": "synthetic_conflict"}], {},
        {"meeting_date": MetadataValue("2026-02-01", 0.75, "high")},
    )
    result = CSEAdapter(CSEAdapterInput(
        SUBJECT, NOW, metadata_records=(record,), meetings=(meeting(),)
    )).adapt()
    assert len(result.reasoning_conflicts) == 1
    assert result.reasoning_conflicts[0].arbitrated is False
    assert result.confidence.level.value == "moderate"


def test_outputs_feed_evidence_graph_reasoning_and_conflict_resolution():
    adapted = CSEAdapter(CSEAdapterInput(
        SUBJECT, NOW, meetings=(meeting(),), votes=(vote(),)
    )).adapt()
    first = adapted.evidence[0]
    graph = EvidenceGraph.empty(EntityId("graph-cse")).add_node(EvidenceNode(
        EntityId("node-cse"), GraphNodeType.EVIDENCE, first.evidence_id
    ))
    reasoning = GenericReasoningPipeline().reason(
        EntityId("reasoning-cse"), adapted.evidence, SUBJECT,
        (FactType("cse_meeting"),), NOW,
    )
    resolution = GenericConflictResolutionEngine().resolve(
        EntityId("resolution-cse"), reasoning, NOW,
        evidence_graph=graph, evidence=adapted.evidence, findings=adapted.findings,
    )
    assert reasoning.facts.facts
    assert resolution.source_reasoning_report == reasoning.report_id
