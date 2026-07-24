from __future__ import annotations

import json

import pytest

from automation.official_knowledge import additional_metadata_feed as feed
from automation.official_knowledge.connectors.anact.anact_platform import (
    ANACT_PLATFORM_CONTRACT,
    ANACT_REGISTRY,
)
from automation.official_knowledge.connectors.carsat.carsat_platform import (
    CARSAT_PLATFORM_CONTRACT,
    CARSAT_REGISTRY,
)
from automation.official_knowledge.connectors.france_chimie.france_chimie_platform import (
    FRANCE_CHIMIE_PLATFORM_CONTRACT,
    FRANCE_CHIMIE_REGISTRY,
)
from automation.official_knowledge.document_registry import (
    DocumentStatus,
    JsonDocumentStorage,
)
from automation.official_knowledge.source_registry import get_source


def test_existing_connector_platform_contracts_remain_registered_and_metadata_only():
    for connector_id, contract, registry in (
        ("anact", ANACT_PLATFORM_CONTRACT, ANACT_REGISTRY),
        ("carsat", CARSAT_PLATFORM_CONTRACT, CARSAT_REGISTRY),
        ("france_chimie", FRANCE_CHIMIE_PLATFORM_CONTRACT, FRANCE_CHIMIE_REGISTRY),
    ):
        assert registry.get(connector_id) is contract
        assert contract.enabled is False
        assert contract.document_policy.value == "METADATA_ONLY"
    local_law = get_source("alsace_moselle_local_law")
    assert local_law.connector_status == "architecture_only"
    assert local_law.authority_level == "primary_law"


def test_catalogues_are_non_empty_unique_https_and_content_free():
    expected = {
        "agirc_arrco": 4,
        "anact": 3,
        "alsace_moselle_local_law": 2,
        "assurance_maladie": 4,
        "carsat": 3,
        "defenseur_droits": 4,
        "france_chimie": 2,
        "ministere_travail": 4,
        "service_public": 4,
        "urssaf": 4,
    }
    for connector_name, count in expected.items():
        documents = feed.load_additional_metadata_sources(connector_name)
        assert len(documents) == count
        assert len({item["canonical_url"] for item in documents}) == count
        assert all(item["canonical_url"].startswith("https://") for item in documents)
        assert all(item["origin"] == connector_name for item in documents)
        serialized = json.dumps(documents, ensure_ascii=False).lower()
        for forbidden in ("content", "full_text", "chunks", ".pdf", "<html", "c:\\"):
            assert forbidden not in serialized


def test_registry_sync_is_persistent_deterministic_and_idempotent(tmp_path):
    path = tmp_path / "registry.json"
    first = feed.synchronize_additional_metadata(path)
    initial_bytes = path.read_bytes()
    second = feed.synchronize_additional_metadata(path)
    assert [(item.connector_name, item.document_count) for item in first] == [
        ("agirc_arrco", 4),
        ("anact", 3),
        ("alsace_moselle_local_law", 2),
        ("assurance_maladie", 4),
        ("carsat", 3),
        ("defenseur_droits", 4),
        ("france_chimie", 2),
        ("ministere_travail", 4),
        ("service_public", 4),
        ("urssaf", 4),
    ]
    assert all(item.last_synchronized_at == "2026-07-24" for item in first)
    assert all(set(item.changes) == {"NEW"} for item in first)
    assert all(set(item.changes) == {"UNCHANGED"} for item in second)
    assert initial_bytes == path.read_bytes()
    records = JsonDocumentStorage(path).load()
    assert len(records) == 34
    assert len({item.document_id for item in records}) == 34
    assert all(item.status is DocumentStatus.ACTIVE for item in records)


def test_incremental_update_and_logical_removal(tmp_path, monkeypatch):
    path = tmp_path / "registry.json"
    feed.synchronize_additional_metadata(path, ("carsat",))
    original = feed._load_catalogue("carsat")
    changed = dict(original["documents"][0], title="Prévention des risques professionnels")
    monkeypatch.setattr(feed, "_load_catalogue", lambda _name: {
        "connector_name": "carsat",
        "last_synchronized_at": "2026-07-25",
        "documents": [changed],
    })
    summary = feed.synchronize_additional_metadata(path, ("carsat",))[0]
    records = JsonDocumentStorage(path).load()
    assert summary.changes == ("REMOVED", "REMOVED", "TITLE_CHANGED")
    assert sum(item.status is DocumentStatus.UPDATED for item in records) == 1
    assert sum(item.status is DocumentStatus.REMOVED for item in records) == 2


def test_identical_runtime_duplicates_are_ignored():
    source = feed.load_additional_metadata_sources("carsat")[0]
    records = feed.validate_additional_runtime_sources(
        "carsat", (source, dict(source)), "2026-07-24"
    )
    assert len(records) == 1


@pytest.mark.parametrize("connector_name", feed.SUPPORTED_ADDITIONAL_FEEDS)
def test_content_fields_are_rejected(connector_name, monkeypatch):
    original = feed._load_catalogue(connector_name)
    polluted = {
        "connector_name": connector_name,
        "last_synchronized_at": "2026-07-24",
        "documents": [dict(original["documents"][0], content="forbidden")],
    }
    monkeypatch.setattr(feed.json, "loads", lambda _value: polluted)
    with pytest.raises(ValueError, match="content is forbidden"):
        feed._load_catalogue(connector_name)
