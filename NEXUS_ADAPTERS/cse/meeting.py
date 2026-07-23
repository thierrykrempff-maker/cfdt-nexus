"""Explicit meeting snapshot mapping without interpreting CSE content."""

from __future__ import annotations

from datetime import datetime, time

from NEXUS_CORE import (
    AcquisitionMethod, ConfidentialityLevel, CustomEvidenceValue, EntityId,
    EntityReference, Evidence, EvidenceId, EvidenceQuality, Provenance, SourceReference,
    SourceType, ValidationStatus,
)

from ._identity import stable_cse_id
from .metadata import CSEMetadataMapper
from .models import CSEMeetingSnapshot


class CSEMeetingMapper:
    def __init__(self, metadata: CSEMetadataMapper | None = None) -> None:
        self._metadata = metadata or CSEMetadataMapper()

    def map(self, meeting: CSEMeetingSnapshot, subject: EntityReference,
            produced_at: datetime) -> Evidence:
        entries = [
            self._metadata.sensitive("meeting_instance", meeting.instance_code),
            self._metadata.technical("agenda_count", len(meeting.agenda_items)),
            self._metadata.technical("participant_count", len(meeting.participant_references)),
            self._metadata.technical("document_count", len(meeting.document_ids)),
            self._metadata.technical("related_minutes_count", len(meeting.related_minutes_ids)),
        ]
        entries.extend(
            self._metadata.sensitive(f"agenda_item_{index}", value)
            for index, value in enumerate(meeting.agenda_items)
        )
        entries.extend(
            self._metadata.sensitive(
                f"participant_ref_{index}", stable_cse_id("participant", value)
            )
            for index, value in enumerate(meeting.participant_references)
        )
        entries.extend(
            self._metadata.sensitive(
                f"related_minutes_{index}", stable_cse_id("document", value)
            )
            for index, value in enumerate(meeting.related_minutes_ids)
        )
        source = SourceReference(
            EntityId(stable_cse_id("meeting_source", meeting.meeting_id)),
            SourceType.CSE_ARCHIVE,
            "CSE_MEETING_SNAPSHOT",
        )
        return Evidence(
            EvidenceId(stable_cse_id("evidence", "meeting", meeting.meeting_id)),
            subject,
            "cse_meeting",
            CustomEvidenceValue("cse_meeting", tuple(entries)),
            None,
            None,
            Provenance(
                source,
                AcquisitionMethod.GENERATED,
                datetime.combine(meeting.meeting_date, time.min, tzinfo=produced_at.tzinfo),
                EntityId(stable_cse_id("trace", "meeting", meeting.meeting_id)),
            ),
            self._metadata.confidence(meeting.confidence),
            EvidenceQuality.CONSISTENT,
            ValidationStatus.PENDING,
            EntityId("adapter-cse"),
            (),
            produced_at,
            ConfidentialityLevel.CONFIDENTIAL,
        )
