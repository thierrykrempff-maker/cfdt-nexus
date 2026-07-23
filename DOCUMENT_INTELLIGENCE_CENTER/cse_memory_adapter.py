"""Metadata-only adapter for existing CSE Memory records."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

from .ingestion_models import (
    ExplicitDocumentLink,
    MeetingMinutesMetadataInput,
)
from .models import DocumentKind, RelationKind


_NON_INDEXABLE_STATUSES = {"ERROR", "UNSUPPORTED", "SKIPPED", "REJECTED"}


def _attribute(record: object, name: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        return record.get(name, default)
    return getattr(record, name, default)


def _metadata_value(metadata: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name not in metadata:
            continue
        item = metadata[name]
        if isinstance(item, Mapping):
            return item.get("value")
        return getattr(item, "value", item)
    return None


def _pseudonymize(source_identifier: str) -> str:
    digest = sha256(f"cse-memory\n{source_identifier}".encode("utf-8")).hexdigest()
    return f"cse-{digest}"


class CSEMemoryMetadataAdapter:
    """Transform CSE Memory metadata without importing paths or content."""

    def adapt(self, record: object) -> MeetingMinutesMetadataInput | None:
        status = str(_attribute(record, "extraction_status", "")).upper()
        if status in _NON_INDEXABLE_STATUSES:
            return None
        metadata = _attribute(record, "metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("CSE_METADATA_INVALID: metadata mapping is required")
        source_id = str(
            _attribute(record, "document_id")
            or _attribute(record, "source_document_id")
            or ""
        ).strip()
        title = str(_metadata_value(metadata, "title", "document_title") or "").strip()
        instance = str(
            _metadata_value(metadata, "instance", "cse_instance", "body") or ""
        ).strip()
        if not source_id or not title or not instance:
            raise ValueError(
                "CSE_METADATA_INCOMPLETE: identifier, title and instance are required"
            )
        raw_kind = str(
            _metadata_value(metadata, "document_kind", "document_type") or "CSE_MINUTES"
        ).upper()
        kind = (
            DocumentKind.CSSCT_MINUTES
            if "CSSCT" in raw_kind
            else DocumentKind.CSE_MINUTES
        )
        references = _metadata_value(
            metadata,
            "agreement_document_ids",
            "agreement_references",
        ) or ()
        if isinstance(references, str):
            references = (references,)
        links = tuple(
            ExplicitDocumentLink(
                target_document_id=str(reference),
                relation_kind=RelationKind.REFERENCES,
            )
            for reference in references
        )
        warnings = tuple(
            sorted(
                {
                    str(warning)
                    for warning in _attribute(record, "warnings", ())
                    if str(warning).strip()
                }
            )
        )
        confidence = _metadata_value(metadata, "confidence")
        return MeetingMinutesMetadataInput(
            pseudonymous_id=_pseudonymize(source_id),
            normalized_title=title,
            logical_provenance="CSE_MEMORY_METADATA",
            document_date=_metadata_value(
                metadata,
                "meeting_date",
                "document_date",
                "date",
            ),
            instance=instance,
            document_kind=kind,
            agreement_links=links,
            confidence=float(confidence) if confidence is not None else 1.0,
            warnings=warnings,
        )
