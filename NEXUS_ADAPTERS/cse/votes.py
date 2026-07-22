"""Vote projection preserving declared counts and result without interpretation."""

from __future__ import annotations

from datetime import datetime

from NEXUS_CORE import (
    AcquisitionMethod, ConfidentialityLevel, CustomEvidenceValue, EntityId,
    EntityReference, Evidence, EvidenceId, EvidenceQuality, Finding, FindingId,
    FindingSeverity, FindingStatus, FindingType, Provenance, SourceReference,
    SourceType, ValidationStatus,
)

from ._identity import stable_cse_id
from .metadata import CSEMetadataMapper
from .models import CSEVoteSnapshot


class CSEVoteMapper:
    def __init__(self, metadata: CSEMetadataMapper | None = None) -> None:
        self._metadata = metadata or CSEMetadataMapper()

    def map(self, vote: CSEVoteSnapshot, subject: EntityReference,
            produced_at: datetime) -> tuple[Evidence, Finding]:
        evidence_id = EvidenceId(stable_cse_id("evidence", "vote", vote.vote_id))
        evidence = Evidence(
            evidence_id,
            subject,
            "cse_vote",
            CustomEvidenceValue(
                "cse_vote",
                (
                    self._metadata.sensitive("vote_result", vote.result_code),
                    self._metadata.technical("votes_for", vote.votes_for),
                    self._metadata.technical("votes_against", vote.votes_against),
                    self._metadata.technical("abstentions", vote.abstentions),
                ),
            ),
            None,
            None,
            Provenance(
                SourceReference(
                    EntityId(stable_cse_id("meeting_source", vote.meeting_id)),
                    SourceType.CSE_ARCHIVE,
                    "CSE_VOTE_SNAPSHOT",
                ),
                AcquisitionMethod.GENERATED,
                produced_at,
                EntityId(stable_cse_id("trace", "vote", vote.vote_id)),
            ),
            self._metadata.confidence(1.0),
            EvidenceQuality.CONSISTENT,
            ValidationStatus.PENDING,
            EntityId("adapter-cse"),
            (),
            produced_at,
            ConfidentialityLevel.CONFIDENTIAL,
        )
        finding = Finding(
            FindingId(stable_cse_id("finding", "vote", vote.vote_id)),
            FindingType.OBSERVATION,
            FindingSeverity.INFO,
            FindingStatus.OPEN,
            "CSE_VOTE_RECORDED",
            (evidence_id,),
        )
        return evidence, finding
