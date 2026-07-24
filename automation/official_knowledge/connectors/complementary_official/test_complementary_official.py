from __future__ import annotations

from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_states import ConnectorState
from automation.official_knowledge.additional_metadata_feed import (
    load_additional_metadata_sources,
    validate_additional_runtime_sources,
)

from . import (
    COMPLEMENTARY_CONNECTOR_CONTRACTS,
    COMPLEMENTARY_CONNECTOR_REGISTRY,
    COMPLEMENTARY_CONNECTOR_SPECS,
    ComplementaryOfficialConnector,
)


EXPECTED = {
    "agirc_arrco": 4,
    "assurance_maladie": 4,
    "defenseur_droits": 4,
    "ministere_travail": 4,
    "service_public": 4,
    "urssaf": 4,
}


def test_connector_platform_contracts_are_registered_validated_and_inactive():
    assert COMPLEMENTARY_CONNECTOR_REGISTRY.list_ids() == tuple(sorted(EXPECTED))
    for connector_id, contract in COMPLEMENTARY_CONNECTOR_CONTRACTS.items():
        assert COMPLEMENTARY_CONNECTOR_REGISTRY.get(connector_id) is contract
        assert contract.state is ConnectorState.VALIDATED
        assert contract.enabled is False
        assert contract.document_policy is DocumentPolicy.METADATA_ONLY
        assert contract.capabilities == frozenset({Capability.MANUAL})
        assert contract.security.network_disabled_by_default is True


def test_catalogues_produce_stable_public_metadata():
    for connector_id, count in EXPECTED.items():
        first = validate_additional_runtime_sources(
            connector_id,
            load_additional_metadata_sources(connector_id),
            "2026-07-24",
        )
        second = validate_additional_runtime_sources(
            connector_id,
            load_additional_metadata_sources(connector_id),
            "2026-07-24",
        )
        assert first == second
        assert len(first) == count
        assert len({item.document_id for item in first}) == count
        assert all(item.canonical_url.startswith("https://") for item in first)
        assert all(item.connector_name == connector_id for item in first)


def test_domains_are_strict_and_non_official_hosts_are_rejected():
    for connector_id, spec in COMPLEMENTARY_CONNECTOR_SPECS.items():
        source = dict(load_additional_metadata_sources(connector_id)[0])
        source["canonical_url"] = "https://example.org/not-official"
        try:
            validate_additional_runtime_sources(
                connector_id,
                (source,),
                "2026-07-24",
            )
        except ValueError:
            continue
        raise AssertionError(f"unofficial domain accepted for {spec.connector_id}")


def test_content_and_incomplete_metadata_are_rejected():
    connector = ComplementaryOfficialConnector("service_public")
    valid = {
        "url": "https://www.service-public.fr/particuliers/vosdroits/F2339",
        "title": "Modification du contrat",
        "category": "contrat",
        "family": "demarches",
        "document_type": "fiche_pratique",
    }
    for invalid in (
        dict(valid, content="forbidden"),
        {key: value for key, value in valid.items() if key != "title"},
    ):
        try:
            connector.validate_metadata((invalid,), "2026-07-24")
        except ValueError:
            continue
        raise AssertionError("invalid complementary metadata accepted")


def test_identical_duplicates_are_idempotently_collapsed():
    source = load_additional_metadata_sources("defenseur_droits")[0]
    records = validate_additional_runtime_sources(
        "defenseur_droits",
        (source, dict(source)),
        "2026-07-24",
    )
    assert len(records) == 1
