from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeCoreIntegration,
    RuntimeCoreIntegrationInput,
    RuntimeIntegrationConfig,
    RuntimeMode,
    RuntimeOfficialConnectorsConfig,
)
from NEXUS_RUNTIME_INTEGRATION.official_connectors_runtime import (
    RuntimeOfficialConnectorsIntegration,
)


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def integrate(query: str):
    return RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True),
        clock=lambda: NOW,
    ).integrate({
        "query": query,
        "generated_at": NOW.isoformat(),
        "route": {"domains": ["droit_travail"]},
        "sources": [],
    })


@pytest.mark.parametrize(
    ("query", "connector_id", "document_count"),
    (
        (
            "Je subis une discrimination syndicale, que dit le Défenseur des droits ?",
            "defenseur_droits",
            4,
        ),
        (
            "Quelle est la procédure de licenciement expliquée par le ministère du Travail ?",
            "ministere_travail",
            4,
        ),
        (
            "Quelle démarche salarié suivre sur Service-Public pour modifier mon contrat ?",
            "service_public",
            4,
        ),
    ),
)
def test_relevant_scenario_activates_connector_and_citations(
    query,
    connector_id,
    document_count,
):
    result = integrate(query)
    selected = {item.descriptor.connector_id: item for item in result.inputs}
    assert connector_id in selected
    assert len(selected[connector_id].response.documents) == document_count
    assert result.diagnostics.connector_runtime_fallback is None
    assert all(
        document.title and document.source_url
        for document in selected[connector_id].response.documents
    )


def test_non_relevant_payroll_question_activates_none():
    result = integrate("Quel est le montant net imposable de cette prime ?")
    assert result.inputs == ()
    assert result.diagnostics.connector_runtime_called is False


def test_overlapping_rights_question_merges_sources_without_duplicates():
    result = integrate(
        "Harcèlement au travail : quelle démarche sur Service-Public et que recommande "
        "le Défenseur des droits ?"
    )
    assert result.diagnostics.connectors_used == (
        "defenseur_droits",
        "service_public",
    )
    identities = [
        document.external_id
        for item in result.inputs
        for document in item.response.documents
    ]
    assert len(identities) == len(set(identities))


def test_hierarchy_categories_and_metadata_only_are_preserved():
    result = integrate(
        "Comparer le Défenseur des droits, le ministère du Travail et Service-Public"
    )
    categories = {
        item.descriptor.connector_id: item.source.category.value
        for item in result.inputs
    }
    assert categories == {
        "defenseur_droits": "INDEPENDENT_AUTHORITY",
        "ministere_travail": "ADMINISTRATIVE_DOCTRINE",
        "service_public": "OTHER_OFFICIAL",
    }
    for item in result.inputs:
        assert all(
            document.content is None and document.excerpt is None
            for document in item.response.documents
        )


def test_all_three_sources_pass_through_connector_adapter_and_core():
    answer = {
        "query": "Comparer le Défenseur des droits, le ministère du Travail et Service-Public",
        "generated_at": NOW.isoformat(),
        "route": {"domains": ["droit_travail"]},
        "sources": [],
    }
    official = RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True),
        clock=lambda: NOW,
    ).integrate(answer)
    result = RuntimeCoreIntegration(
        RuntimeIntegrationConfig(True),
        clock=lambda: NOW,
    ).integrate(RuntimeCoreIntegrationInput(
        answer,
        {"active": True, "ce_qui_est_certain": ["Constat public."]},
        {"active": False},
        {},
        official.inputs,
        True,
    ))
    assert result.runtime_mode is RuntimeMode.CORE_V3
    assert result.diagnostics.connector_count == 3
    assert result.diagnostics.connector_evidence_count == 12
    assert set(result.selected_experts) >= {
        "connector_defenseur_droits",
        "connector_ministere_travail",
        "connector_service_public",
    }


def test_runtime_output_is_confidential_and_network_free(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "socket",
        lambda *_args, **_kwargs: (
            _ for _ in ()
        ).throw(AssertionError("network forbidden")),
    )
    result = integrate(
        "Comparer le Défenseur des droits, le ministère du Travail et Service-Public"
    )
    serialized = json.dumps(result.to_dict(), ensure_ascii=False).lower()
    for forbidden in (
        "c:\\", "/home/", "/users/", "chunk_", "storage_id",
        "iban", "nir", "email", "telephone",
    ):
        assert forbidden not in serialized
