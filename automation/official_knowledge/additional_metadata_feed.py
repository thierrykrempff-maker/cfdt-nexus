"""Validated metadata-only feed for the remaining existing official sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from automation.official_knowledge.connectors.anact import (
    AnactResource,
    AnactResourceType,
    AnactTheme,
    GeographicScope,
)
from automation.official_knowledge.connectors.carsat import CarsatMetadata
from automation.official_knowledge.connectors.complementary_official import (
    COMPLEMENTARY_CONNECTOR_SPECS,
    ComplementaryOfficialConnector,
)
from automation.official_knowledge.connectors.france_chimie import FranceChimieConnector
from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentRegistry,
    DocumentStatus,
    DocumentValidator,
    JsonDocumentStorage,
    stable_document_id,
)


SUPPORTED_ADDITIONAL_FEEDS = (
    "agirc_arrco",
    "anact",
    "alsace_moselle_local_law",
    "assurance_maladie",
    "carsat",
    "defenseur_droits",
    "france_chimie",
    "ministere_travail",
    "service_public",
    "urssaf",
)
_ROOT = Path(__file__).resolve().parents[2]
_CATALOGUES = {
    "agirc_arrco": _ROOT / "automation/official_knowledge/connectors/complementary_official/agirc_arrco_metadata.json",
    "anact": _ROOT / "automation/official_knowledge/connectors/anact/public_metadata.json",
    "alsace_moselle_local_law": _ROOT / "automation/local_law/public_metadata.json",
    "assurance_maladie": _ROOT / "automation/official_knowledge/connectors/complementary_official/assurance_maladie_metadata.json",
    "carsat": _ROOT / "automation/official_knowledge/connectors/carsat/public_metadata.json",
    "defenseur_droits": _ROOT / "automation/official_knowledge/connectors/complementary_official/defenseur_droits_metadata.json",
    "france_chimie": _ROOT / "automation/official_knowledge/connectors/france_chimie/public_metadata.json",
    "ministere_travail": _ROOT / "automation/official_knowledge/connectors/complementary_official/ministere_travail_metadata.json",
    "service_public": _ROOT / "automation/official_knowledge/connectors/complementary_official/service_public_metadata.json",
    "urssaf": _ROOT / "automation/official_knowledge/connectors/complementary_official/urssaf_metadata.json",
}
_DOMAINS = {
    "agirc_arrco": COMPLEMENTARY_CONNECTOR_SPECS["agirc_arrco"].official_domains,
    "anact": frozenset({"www.anact.fr"}),
    "alsace_moselle_local_law": frozenset({"www.legifrance.gouv.fr"}),
    "assurance_maladie": COMPLEMENTARY_CONNECTOR_SPECS["assurance_maladie"].official_domains,
    "carsat": frozenset({"www.carsat-alsacemoselle.fr"}),
    "defenseur_droits": COMPLEMENTARY_CONNECTOR_SPECS["defenseur_droits"].official_domains,
    "france_chimie": frozenset({"www.francechimie.fr"}),
    "ministere_travail": COMPLEMENTARY_CONNECTOR_SPECS["ministere_travail"].official_domains,
    "service_public": COMPLEMENTARY_CONNECTOR_SPECS["service_public"].official_domains,
    "urssaf": COMPLEMENTARY_CONNECTOR_SPECS["urssaf"].official_domains,
}
_FORBIDDEN_FIELDS = frozenset({
    "body", "chunks", "content", "document_path", "excerpt", "full_text",
    "html", "pdf", "raw_html", "summary", "text",
})


@dataclass(frozen=True)
class AdditionalMetadataSyncSummary:
    connector_name: str
    document_count: int
    citation_count: int
    last_synchronized_at: str
    changes: tuple[str, ...]


def load_additional_metadata_sources(connector_name: str) -> tuple[dict[str, Any], ...]:
    payload = _load_catalogue(connector_name)
    synchronized_at = str(payload["last_synchronized_at"])
    records = _validate_documents(connector_name, tuple(payload["documents"]), synchronized_at)
    return tuple(_runtime_source(record, synchronized_at) for record in records)


def validate_additional_runtime_sources(
    connector_name: str,
    sources: tuple[Mapping[str, Any], ...],
    synchronized_at: str,
) -> tuple[DocumentRecord, ...]:
    """Validate router-injected metadata with the same public connector rules."""
    normalized = tuple({
        "url": item.get("canonical_url") or item.get("url") or item.get("url_or_id"),
        "title": item.get("title") or item.get("document"),
        "publication_date": item.get("publication_date") or item.get("date"),
        "category": item.get("category"),
        "family": item.get("family"),
        "document_type": item.get("document_type"),
        "language": item.get("language", "fr"),
        **({"reference": item.get("reference")} if item.get("reference") else {}),
        **({"aract_name": item.get("aract_name")} if item.get("aract_name") else {}),
    } for item in sources)
    return _validate_documents(connector_name, normalized, synchronized_at)


def synchronize_additional_metadata(
    registry_path: Path,
    connector_names: tuple[str, ...] = SUPPORTED_ADDITIONAL_FEEDS,
) -> tuple[AdditionalMetadataSyncSummary, ...]:
    if not isinstance(connector_names, tuple) or any(name not in SUPPORTED_ADDITIONAL_FEEDS for name in connector_names):
        raise ValueError("unsupported additional official feed")
    registry = DocumentRegistry(JsonDocumentStorage(Path(registry_path)), DocumentValidator(_DOMAINS))
    summaries = []
    for connector_name in connector_names:
        payload = _load_catalogue(connector_name)
        synchronized_at = str(payload["last_synchronized_at"])
        records = _validate_documents(connector_name, tuple(payload["documents"]), synchronized_at)
        incoming = {item.document_id for item in records}
        changes = []
        for item in records:
            previous = registry.find_document(item.document_id)
            if previous:
                item = DocumentRecord(
                    **{
                        **item.to_dict(),
                        "first_seen": previous.first_seen,
                        "last_modified_metadata": previous.last_modified_metadata,
                        "status": previous.status,
                    }
                )
                change = registry.update_document(item)
            else:
                change = registry.register_document(item)
            changes.append(change.kind.value)
        for previous in registry.find_by_connector(connector_name):
            if previous.document_id not in incoming and previous.status is not DocumentStatus.REMOVED:
                changes.append(registry.mark_removed(previous.document_id, checked_on=synchronized_at).kind.value)
        summaries.append(AdditionalMetadataSyncSummary(
            connector_name,
            len(records),
            len(records),
            synchronized_at,
            tuple(sorted(changes)),
        ))
    return tuple(summaries)


def _load_catalogue(connector_name: str) -> Mapping[str, Any]:
    if connector_name not in SUPPORTED_ADDITIONAL_FEEDS:
        raise ValueError("unsupported additional official feed")
    payload = json.loads(_CATALOGUES[connector_name].read_text(encoding="utf-8"))
    if set(payload) != {"connector_name", "last_synchronized_at", "documents"}:
        raise ValueError("invalid metadata catalogue")
    if payload["connector_name"] != connector_name or not isinstance(payload["documents"], list) or not payload["documents"]:
        raise ValueError("invalid metadata catalogue")
    if any(not isinstance(item, dict) or _FORBIDDEN_FIELDS.intersection(item) for item in payload["documents"]):
        raise ValueError("document content is forbidden")
    return payload


def _validate_documents(
    connector_name: str,
    documents: tuple[Mapping[str, Any], ...],
    synchronized_at: str,
) -> tuple[DocumentRecord, ...]:
    if connector_name == "carsat":
        metadata = tuple(CarsatMetadata.create(
            canonical_url=str(item["url"]), title=str(item["title"]),
            publication_date=item.get("publication_date"), category=str(item["category"]),
            family=str(item["family"]), document_type=str(item["document_type"]),
            discovered_at=synchronized_at, language=str(item.get("language", "fr")),
            reference=item.get("reference"),
        ) for item in documents)
        records = tuple(_record_from_metadata(connector_name, item, synchronized_at) for item in metadata)
    elif connector_name == "france_chimie":
        metadata = FranceChimieConnector().validate_injected_metadata(
            tuple(dict(item, discovered_at=synchronized_at) for item in documents),
            allowed_domains=_DOMAINS[connector_name],
            limit=100,
        )
        records = tuple(_record_from_metadata(connector_name, item, synchronized_at) for item in metadata)
    elif connector_name == "anact":
        records = tuple(_anact_record(item, synchronized_at) for item in documents)
    elif connector_name == "alsace_moselle_local_law":
        records = tuple(_plain_record(connector_name, item, synchronized_at) for item in documents)
    elif connector_name in COMPLEMENTARY_CONNECTOR_SPECS:
        records = ComplementaryOfficialConnector(connector_name).validate_metadata(
            documents,
            synchronized_at,
        )
    else:
        raise ValueError("unsupported additional official feed")
    validator = DocumentValidator({connector_name: _DOMAINS[connector_name]})
    for record in records:
        validator.validate_new(record)
    unique: dict[str, DocumentRecord] = {}
    for record in records:
        previous = unique.get(record.document_id)
        if previous is not None and previous != record:
            raise ValueError("conflicting duplicate document identity")
        unique[record.document_id] = record
    return tuple(sorted(unique.values(), key=lambda item: item.document_id))


def _record_from_metadata(connector_name: str, item: object, checked_on: str) -> DocumentRecord:
    return DocumentRecord(
        document_id=str(getattr(item, "document_id")),
        connector_name=connector_name,
        canonical_url=str(getattr(item, "canonical_url")),
        title=str(getattr(item, "title")),
        category=str(getattr(item, "category")),
        family=_value(getattr(item, "family")),
        document_type=_value(getattr(item, "document_type")),
        publication_date=getattr(item, "publication_date"),
        first_seen=checked_on,
        last_checked=checked_on,
        last_modified_metadata=checked_on,
        language=str(getattr(item, "language")),
        provenance=str(getattr(item, "provenance")),
    )


def _anact_record(item: Mapping[str, Any], checked_on: str) -> DocumentRecord:
    scope = GeographicScope(str(item["family"]))
    resource = AnactResource(
        resource_id=str(item.get("reference") or stable_document_id("anact", str(item["url"]))),
        source_id="anact_national",
        resource_type=AnactResourceType(str(item["document_type"])),
        theme=AnactTheme(str(item["category"])),
        title=str(item["title"]),
        canonical_url=str(item["url"]),
        published_at=item.get("publication_date"),
        collected_at=datetime.fromisoformat(checked_on).replace(tzinfo=timezone.utc),
        scope=scope,
        aract_name=item.get("aract_name") or (
            "Réseau régional ANACT-ARACT" if scope is GeographicScope.REGIONAL else None
        ),
        language=str(item.get("language", "fr")),
        official_content=True,
    )
    return resource.to_document_record(checked_on=checked_on)


def _plain_record(connector_name: str, item: Mapping[str, Any], checked_on: str) -> DocumentRecord:
    url = str(item["url"])
    return DocumentRecord(
        document_id=stable_document_id(connector_name, url),
        connector_name=connector_name,
        canonical_url=url,
        title=str(item["title"]),
        category=str(item["category"]),
        family=str(item["family"]),
        document_type=str(item["document_type"]),
        publication_date=item.get("publication_date"),
        first_seen=checked_on,
        last_checked=checked_on,
        last_modified_metadata=checked_on,
        language=str(item.get("language", "fr")),
        provenance=connector_name,
    )


def _runtime_source(record: DocumentRecord, synchronized_at: str) -> dict[str, Any]:
    return {
        "origin": record.connector_name,
        "canonical_url": record.canonical_url,
        "title": record.title,
        "publication_date": record.publication_date,
        "category": record.category,
        "family": record.family,
        "document_type": record.document_type,
        "language": record.language,
        "provenance": record.provenance,
        "discovered_at": synchronized_at,
    }


def _value(value: object) -> str:
    return str(getattr(value, "value", value))
