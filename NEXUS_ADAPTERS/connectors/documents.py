"""Generic connector document snapshots to Core document references."""

from __future__ import annotations

from NEXUS_CORE import (
    ConfidentialityLevel, DocumentId, DocumentMetadata, DocumentReference, DocumentSource,
)

from .identity import stable_connector_id
from .metadata import ConnectorMetadataMapper
from .models import ConnectorAdapterInput, ConnectorDocumentSnapshot
from .normalization import ConnectorSourceNormalizer
from .provenance import ConnectorProvenanceMapper


class ConnectorDocumentMapper:
    def __init__(self) -> None:
        self._normalizer = ConnectorSourceNormalizer()
        self._metadata = ConnectorMetadataMapper()
        self._provenance = ConnectorProvenanceMapper(self._normalizer)

    def map(self, source: ConnectorAdapterInput) -> tuple[DocumentReference, ...]:
        return tuple(self.map_one(source, item) for item in source.response.documents)

    def map_one(self, source: ConnectorAdapterInput,
                item: ConnectorDocumentSnapshot) -> DocumentReference:
        document_type = self._normalizer.document_type(item.document_type)
        identity = self._identity_material(item)
        entries = list(self._metadata.map(item.metadata))
        for key, value in (
            ("official_reference", item.official_reference),
            ("updated_at", item.updated_at),
            ("document_version", item.version),
            ("document_author", item.author),
            ("source_url", item.source_url),
            ("fingerprint", item.fingerprint),
            ("validity_status", item.validity_status),
            ("original_document_type", item.document_type),
        ):
            if value is not None:
                entries.append(self._metadata.entry(key, value))
        return DocumentReference(
            DocumentId(stable_connector_id(
                "document", source.descriptor.connector_id, identity
            )),
            document_type,
            DocumentSource(self._provenance.map(source, item).source),
            DocumentMetadata(
                document_type, item.title, item.publication_date, item.language, tuple(entries)
            ),
            ConfidentialityLevel.PUBLIC if source.source.official else ConfidentialityLevel.INTERNAL,
        )

    @staticmethod
    def _identity_material(item: ConnectorDocumentSnapshot) -> str:
        return next(
            (value for value in (
                item.external_id, item.official_reference, item.source_url,
                item.fingerprint, item.title,
            ) if value),
            "missing_document_identity",
        )
