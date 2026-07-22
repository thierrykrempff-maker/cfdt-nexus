from __future__ import annotations

from datetime import datetime, timezone
import json

import NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime as runtime_module
from NEXUS_RUNTIME_INTEGRATION import RuntimeOfficialConnectorsConfig
from NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime import (
    RuntimeOfficialConnectorsIntegration,
)


NOW = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def answer():
    return {
        "query": "Prévention, données personnelles et dialogue social",
        "generated_at": NOW.isoformat(),
        "sources": [
            {
                "origin": "cnil", "url": "https://www.cnil.fr/fr/guide-synthetique",
                "title": "Guide synthétique", "publication_date": "2026-01-10",
                "category": "guide", "family": "guide", "document_type": "guide",
                "mime_type": "text/html", "discovered_at": "2026-07-22",
            },
            {
                "origin": "dreets_grand_est",
                "url": "https://grand-est.dreets.gouv.fr/fiche-synthetique",
                "title": "Fiche synthétique", "publication_date": "2026-02-11",
                "category": "fiche", "family": "cse", "document_type": "fiche",
                "mime_type": "text/html",
            },
            {
                "origin": "inrs", "url": "https://www.inrs.fr/publications/guide-synthetique",
                "title": "Prévention synthétique", "publication_date": "2026-03-12",
                "category": "prevention", "family": "prevention", "document_type": "guide",
                "reference": "ED 0000",
            },
        ],
    }


def integration(enabled=True):
    ticks = iter((20.0, 20.007))
    return RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(enabled), clock=lambda: NOW, timer=lambda: next(ticks)
    )


def test_feature_flag_is_disabled_by_default_and_independent():
    assert RuntimeOfficialConnectorsConfig.from_env({}).enabled is False
    assert RuntimeOfficialConnectorsConfig.from_env({
        "NEXUS_CORE_RUNTIME_ENABLED": "true"
    }).enabled is False
    assert RuntimeOfficialConnectorsConfig.from_env({
        "NEXUS_OFFICIAL_CONNECTORS_RUNTIME_ENABLED": "true"
    }).enabled is True
    assert integration(False).integrate(answer()).inputs == ()


def test_existing_public_connector_apis_are_really_called(monkeypatch):
    calls = {"cnil": 0, "dreets_grand_est": 0, "inrs": 0}

    def tracked(connector_id, original):
        class Tracked(original):
            def discover_metadata(self, *args, **kwargs):
                calls[connector_id] += 1
                return super().discover_metadata(*args, **kwargs)

        return Tracked

    for name, original in (
        ("CnilConnector", runtime_module.CnilConnector),
        ("DreetsGrandEstConnector", runtime_module.DreetsGrandEstConnector),
        ("InrsConnector", runtime_module.InrsConnector),
    ):
        connector_id = {
            "CnilConnector": "cnil", "DreetsGrandEstConnector": "dreets_grand_est",
            "InrsConnector": "inrs",
        }[name]

        monkeypatch.setattr(runtime_module, name, tracked(connector_id, original))

    result = integration().integrate(answer())
    assert calls == {"cnil": 1, "dreets_grand_est": 1, "inrs": 1}
    assert tuple(item.descriptor.connector_id for item in result.inputs) == (
        "cnil", "dreets_grand_est", "inrs"
    )
    assert result.diagnostics.connector_runtime_called is True
    assert result.diagnostics.connector_runtime_ms == 7
    assert result.diagnostics.connectors_used == ("cnil", "dreets_grand_est", "inrs")
    for connector_input in result.inputs:
        assert len(connector_input.response.documents) == 1
        snapshot = connector_input.response.documents[0]
        assert snapshot.content is None
        assert snapshot.excerpt is None
        assert ("metadata_only", True) in snapshot.metadata


def test_irrelevant_sources_do_not_call_connectors():
    result = integration().integrate({
        "query": "Question", "sources": [{"origin": "legifrance_code_travail"}]
    })
    assert result.inputs == ()
    assert result.diagnostics.connector_runtime_called is False


def test_one_connector_failure_closes_the_whole_official_batch_without_leak():
    value = answer()
    value["sources"][0]["url"] = "https://private.invalid/Personne-Exemple"
    value["sources"][0]["title"] = "299019999999999 FR7630006000011234567890189"
    result = integration().integrate(value)
    assert result.inputs == ()
    assert result.diagnostics.connector_runtime_fallback == "OFFICIAL_CONNECTOR_RUNTIME_FAILED"
    serialized = json.dumps(result.to_dict())
    for secret in ("Personne-Exemple", "299019999999999", "FR7630006000011234567890189"):
        assert secret not in serialized


def test_only_metadata_sources_are_accepted_and_content_field_cannot_reach_snapshots():
    value = answer()
    value["sources"][2]["content"] = "contenu interdit"
    result = integration().integrate(value)
    assert result.inputs
    serialized = json.dumps(result.to_dict())
    assert "contenu interdit" not in serialized


def test_integration_performs_no_network_access(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "socket",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")),
    )
    result = integration().integrate(answer())
    assert result.diagnostics.connectors_used == ("cnil", "dreets_grand_est", "inrs")
