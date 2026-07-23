"""Traceable provenance mapping without exposing connector credentials."""

from __future__ import annotations

from NEXUS_CORE import AcquisitionMethod, EntityId, Provenance, SourceReference

from .identity import stable_connector_id
from .models import ConnectorAdapterInput, ConnectorDocumentSnapshot
from .normalization import ConnectorSourceNormalizer


class ConnectorProvenanceMapper:
    def __init__(self, normalizer: ConnectorSourceNormalizer | None = None) -> None:
        self._normalizer = normalizer or ConnectorSourceNormalizer()

    def map(self, source: ConnectorAdapterInput,
            document: ConnectorDocumentSnapshot | None = None) -> Provenance:
        external = document.external_id if document and document.external_id else "response"
        source_reference = SourceReference(
            EntityId(stable_connector_id(
                "source", source.descriptor.connector_id, source.source.source_id
            )),
            self._normalizer.source_type(source.source.category),
            "CONNECTOR_SOURCE",
        )
        return Provenance(
            source_reference,
            AcquisitionMethod.CONNECTOR,
            source.acquired_at,
            EntityId(stable_connector_id(
                "trace", source.descriptor.connector_id, source.query.query_id,
                source.descriptor.version, external,
            )),
        )
