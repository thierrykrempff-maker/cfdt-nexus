from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone

import pytest

from NEXUS_ADAPTERS.connectors import (
    ConnectorAdapterInput, ConnectorCapability, ConnectorDescriptor,
    ConnectorDocumentSnapshot, ConnectorQuerySnapshot, ConnectorResponseSnapshot,
    ConnectorResponseStatus, ConnectorSourceCategory, ConnectorSourceSnapshot,
)
from NEXUS_ADAPTERS.connectors.identity import stable_connector_id


NOW = datetime(2026, 3, 4, tzinfo=timezone.utc)


def synthetic_input(*, documents=(), score=0.8, category=ConnectorSourceCategory.LEGISLATION,
                    errors=(), status=ConnectorResponseStatus.SUCCEEDED):
    return ConnectorAdapterInput(
        ConnectorDescriptor("synthetic_connector", "1.0", (ConnectorCapability.DOCUMENTS,)),
        ConnectorSourceSnapshot("synthetic_source", "SYNTHETIC_SOURCE", category, True,
                                "https://example.invalid/source"),
        ConnectorQuerySnapshot("query-one", "SYNTHETIC_QUERY"),
        ConnectorResponseSnapshot(
            "response-one", status, documents=documents,
            technical_errors=errors, source_confidence=score, duration_ms=5,
        ),
        NOW,
    )


def synthetic_document(external_id="doc-one", *, content="synthetic public text"):
    return ConnectorDocumentSnapshot(
        external_id, "synthetic_source", "LEGISLATION", "Synthetic document",
        "REF-SYNTHETIC", date(2026, 1, 1), NOW, "1.0", "Synthetic authority",
        "https://example.invalid/document", "fr", content=content,
        fingerprint="abcdef", validity_status="active",
    )


def test_models_are_immutable():
    value = synthetic_input(documents=(synthetic_document(),))
    with pytest.raises(FrozenInstanceError):
        value.schema_version = "changed"


def test_identifiers_are_stable_and_order_independent():
    first = stable_connector_id("document", "connector", "external-one")
    assert first == stable_connector_id("document", "connector", "external-one")
    assert first != stable_connector_id("document", "connector", "external-two")


def test_snapshots_hold_multiple_documents_without_mutable_collections():
    value = synthetic_input(documents=(synthetic_document(), synthetic_document("doc-two")))
    assert len(value.response.documents) == 2
    assert isinstance(value.response.documents, tuple)
