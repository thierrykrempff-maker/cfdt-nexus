from __future__ import annotations

from datetime import datetime, timezone
import json

from NEXUS_RUNTIME_INTEGRATION import RuntimeOfficialConnectorsConfig
from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeCoreIntegration,
    RuntimeCoreIntegrationInput,
    RuntimeIntegrationConfig,
    RuntimeMode,
)
from NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime import (
    RuntimeOfficialConnectorsIntegration,
)


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def integrate(query: str, domains: tuple[str, ...] = ()):
    return RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate({
        "query": query,
        "generated_at": NOW.isoformat(),
        "route": {"domains": domains},
        "sources": [],
    })


def test_each_relevant_connector_is_selected_with_exploitable_citations():
    cases = (
        ("Comment préparer mon départ anticipé avec la CARSAT ?", (), "carsat", 3),
        ("Que prévoit la convention collective Chimie sur la classification ?", (), "france_chimie", 2),
        ("Comment engager une démarche QVCT avec l'ANACT ?", (), "anact", 3),
        ("Quel repos dominical prévoit le droit local Alsace-Moselle ?", (), "alsace_moselle_local_law", 2),
    )
    for query, domains, connector_id, count in cases:
        result = integrate(query, domains)
        assert result.diagnostics.connector_runtime_fallback is None
        selected = {item.descriptor.connector_id: item for item in result.inputs}
        assert connector_id in selected
        documents = selected[connector_id].response.documents
        assert len(documents) == count
        assert all(item.title and item.source_url for item in documents)


def test_route_domains_activate_carsat_and_local_law_without_forcing_others():
    retirement = integrate("Préparer mon dossier", ("retraite_penibilite",))
    local = integrate("Règle territoriale applicable", ("droit_local",))
    assert retirement.diagnostics.connectors_used == ("carsat",)
    assert local.diagnostics.connectors_used == ("alsace_moselle_local_law",)


def test_unrelated_question_does_not_activate_additional_connectors():
    result = integrate("Quel est le montant net de cette prime ?", ("paie_remuneration",))
    assert result.inputs == ()
    assert result.diagnostics.connector_runtime_called is False


def test_duplicate_router_metadata_is_deduplicated():
    source = {
        "origin": "carsat",
        "url": "https://www.carsat-alsacemoselle.fr/home/nous-connaitre/presentation-de-la-carsat/missions.html",
        "title": "Missions de la Carsat Alsace-Moselle",
        "category": "retraite_et_santé_au_travail",
        "family": "missions",
        "document_type": "page_institutionnelle",
        "language": "fr",
    }
    payload = {
        "query": "Carsat",
        "generated_at": NOW.isoformat(),
        "route": {"domains": ["retraite_penibilite"]},
        "sources": [source, dict(source)],
    }
    result = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(payload)
    assert len(result.inputs[0].response.documents) == 1


def test_public_snapshots_are_metadata_only_and_confidential():
    result = integrate(
        "Comparer CARSAT, France Chimie, ANACT et droit local Alsace-Moselle"
    )
    assert result.diagnostics.connectors_used == (
        "alsace_moselle_local_law", "anact", "carsat", "france_chimie"
    )
    serialized = json.dumps(result.to_dict(), ensure_ascii=False).lower()
    for item in result.inputs:
        assert all(document.content is None and document.excerpt is None for document in item.response.documents)
    for forbidden in ("c:\\", "/home/", "/users/", "chunk_", "storage_id", "iban", "nir"):
        assert forbidden not in serialized


def test_all_additional_sources_merge_through_connector_adapter_and_core():
    answer = {
        "query": "Comparer CARSAT, France Chimie, ANACT et droit local Alsace-Moselle",
        "generated_at": NOW.isoformat(),
        "route": {"domains": ["multidomaine"]},
        "sources": [],
    }
    official = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True), clock=lambda: NOW
    ).integrate(answer)
    result = RuntimeCoreIntegration(
        RuntimeIntegrationConfig(True), clock=lambda: NOW
    ).integrate(RuntimeCoreIntegrationInput(
        answer,
        {"active": True, "ce_qui_est_certain": ["Constat public."]},
        {"active": False},
        {},
        official.inputs,
        True,
    ))
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.connector_count == 4
    assert result.diagnostics.connector_evidence_count == 10
    assert set(result.selected_experts) >= {
        "connector_anact",
        "connector_alsace_moselle_local_law",
        "connector_carsat",
        "connector_france_chimie",
    }


def test_unit_flow_performs_no_network_access(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "socket",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden")),
    )
    result = integrate("Comment engager une démarche QVCT avec l'ANACT ?")
    assert result.diagnostics.connectors_used == ("anact",)
