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


def integrate(query: str, domains: tuple[str, ...] = ()):
    return RuntimeOfficialConnectorsIntegration(
        RuntimeOfficialConnectorsConfig(True),
        clock=lambda: NOW,
    ).integrate({
        "query": query,
        "generated_at": NOW.isoformat(),
        "route": {"domains": domains},
        "sources": [],
    })


@pytest.mark.parametrize(
    ("query", "connector_id"),
    (
        (
            "Comment la CPAM verse-t-elle les IJSS pendant mon arrêt maladie ?",
            "assurance_maladie",
        ),
        (
            "Quelle assiette de cotisations l'Urssaf applique-t-elle aux avantages en nature ?",
            "urssaf",
        ),
        (
            "Comment mes points de retraite complémentaire Agirc-Arrco sont-ils acquis ?",
            "agirc_arrco",
        ),
    ),
)
def test_context_selects_expected_connector_with_four_citations(query, connector_id):
    result = integrate(query)
    selected = {item.descriptor.connector_id: item for item in result.inputs}
    assert connector_id in selected
    assert len(selected[connector_id].response.documents) == 4
    assert result.diagnostics.connector_runtime_fallback is None
    assert all(
        document.title and document.source_url
        for document in selected[connector_id].response.documents
    )


def test_domain_routes_select_expected_social_and_retirement_sources():
    protection = integrate("Droits applicables", ("protection_sociale",))
    retirement = integrate("Préparer mon départ", ("retraite_penibilite",))
    assert protection.diagnostics.connectors_used == ("assurance_maladie",)
    assert retirement.diagnostics.connectors_used == ("agirc_arrco", "carsat")


def test_multisource_payroll_question_merges_cpam_and_urssaf_without_duplicates():
    result = integrate(
        "Quelles cotisations sociales s'appliquent aux IJSS versées pendant un arrêt maladie ?"
    )
    assert result.diagnostics.connectors_used == ("assurance_maladie", "urssaf")
    identities = [
        document.external_id
        for item in result.inputs
        for document in item.response.documents
    ]
    assert len(identities) == 8
    assert len(identities) == len(set(identities))


def test_unrelated_cse_question_does_not_activate_social_connectors():
    result = integrate("Quel est le délai de consultation du CSE ?", ("cse",))
    assert result.inputs == ()
    assert result.diagnostics.connector_runtime_called is False


def test_all_three_sources_pass_through_connector_adapter_and_core():
    answer = {
        "query": "Comparer CPAM, Urssaf et Agirc-Arrco",
        "generated_at": NOW.isoformat(),
        "route": {"domains": ["multidomaine"]},
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
        "connector_agirc_arrco",
        "connector_assurance_maladie",
        "connector_urssaf",
    }


def test_snapshots_are_metadata_only_confidential_and_network_free(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "socket",
        lambda *_args, **_kwargs: (
            _ for _ in ()
        ).throw(AssertionError("network forbidden")),
    )
    result = integrate("Comparer CPAM, Urssaf et Agirc-Arrco")
    serialized = json.dumps(result.to_dict(), ensure_ascii=False).lower()
    for item in result.inputs:
        assert all(
            document.content is None and document.excerpt is None
            for document in item.response.documents
        )
    for forbidden in (
        "c:\\", "/home/", "/users/", "chunk_", "storage_id",
        "iban", "nir", "email", "telephone",
    ):
        assert forbidden not in serialized
