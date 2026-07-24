"""Strict offline validation facade for complementary public metadata."""

from __future__ import annotations

from typing import Any, Mapping

from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentValidator,
    stable_document_id,
)

from .platform import (
    COMPLEMENTARY_CONNECTOR_CONTRACTS,
    COMPLEMENTARY_CONNECTOR_SPECS,
)


_FORBIDDEN_FIELDS = frozenset({
    "body", "chunks", "content", "document_path", "excerpt", "full_text",
    "html", "pdf", "raw_html", "summary", "text",
})
_REQUIRED_FIELDS = frozenset({
    "url", "title", "category", "family", "document_type",
})


class ComplementaryOfficialConnector:
    """Validate injected public metadata without transport or content access."""

    def __init__(self, connector_id: str) -> None:
        if connector_id not in COMPLEMENTARY_CONNECTOR_SPECS:
            raise ValueError("unsupported complementary connector")
        self.connector_id = connector_id
        self.spec = COMPLEMENTARY_CONNECTOR_SPECS[connector_id]
        self.platform_contract = COMPLEMENTARY_CONNECTOR_CONTRACTS[connector_id]

    def validate_metadata(
        self,
        entries: tuple[Mapping[str, Any], ...],
        synchronized_at: str,
    ) -> tuple[DocumentRecord, ...]:
        validator = DocumentValidator({
            self.connector_id: self.spec.official_domains,
        })
        records: dict[str, DocumentRecord] = {}
        for entry in entries:
            if _FORBIDDEN_FIELDS.intersection(entry):
                raise ValueError("document content is forbidden")
            if not _REQUIRED_FIELDS.issubset(entry):
                raise ValueError("required metadata is missing")
            url = str(entry["url"])
            record = DocumentRecord(
                document_id=stable_document_id(self.connector_id, url),
                connector_name=self.connector_id,
                canonical_url=url,
                title=str(entry["title"]),
                category=str(entry["category"]),
                family=str(entry["family"]),
                document_type=str(entry["document_type"]),
                publication_date=entry.get("publication_date"),
                first_seen=synchronized_at,
                last_checked=synchronized_at,
                last_modified_metadata=synchronized_at,
                language=str(entry.get("language", "fr")),
                provenance=self.spec.display_name,
            )
            validator.validate_new(record)
            previous = records.get(record.document_id)
            if previous is not None and previous != record:
                raise ValueError("conflicting duplicate document identity")
            records[record.document_id] = record
        return tuple(sorted(records.values(), key=lambda item: item.document_id))
