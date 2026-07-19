"""LOT 3A deterministic discovery and activation guard tests."""

from __future__ import annotations

import ast
import inspect

import pytest

from automation.official_knowledge.document_registry import ChangeKind, JsonDocumentStorage

from .dreets_connector import DreetsGrandEstConnector, build_dreets_document_registry
from .dreets_discovery import DreetsDiscoveryItem, DreetsMetadataDiscovery
from .dreets_metadata import DreetsMetadataRefusal


def item(**changes) -> DreetsDiscoveryItem:
    values = {
        "url": "https://grand-est.dreets.gouv.fr/Inspection-du-travail",
        "title": "Inspection du travail",
        "date": "2026-07-20",
        "category": "fiche",
        "family": "inspection_du_travail",
        "document_type": "page_officielle",
        "mime_type": "text/html; charset=utf-8",
    }
    values.update(changes)
    return DreetsDiscoveryItem(**values)


def test_discovery_requires_explicit_activation():
    discovery = DreetsMetadataDiscovery()
    with pytest.raises(DreetsMetadataRefusal) as raised:
        discovery.discover((item(),), discovered_on="2026-07-21")
    assert raised.value.code == "DISCOVERY_NOT_ACTIVATED"


def test_valid_discovery_returns_metadata_only():
    result = DreetsMetadataDiscovery().activate().discover((item(),), discovered_on="2026-07-21")
    assert len(result) == 1
    assert result[0].title == "Inspection du travail"
    assert result[0].discovered_on == "2026-07-21"
    assert set(result[0].to_dict()) == {
        "canonical_url", "title", "date", "category", "family", "document_type",
        "provenance", "language", "discovered_on",
    }


def test_connector_is_officially_activable_for_metadata_only():
    connector = DreetsGrandEstConnector()
    assert connector.metadata_discovery_activable is True
    assert connector.activation_scope == "METADATA_ONLY"
    assert connector.metadata_discovery_enabled is False
    activated = connector.activate_metadata_discovery()
    assert activated.metadata_discovery_enabled is True
    result = activated.discover_metadata((item(),), discovered_on="2026-07-21")
    assert result[0].canonical_url.startswith("https://grand-est.dreets.gouv.fr/")
    assert connector.metadata_discovery_enabled is False


def test_activation_and_batch_types_fail_closed():
    with pytest.raises(TypeError):
        DreetsMetadataDiscovery(activated="yes")  # type: ignore[arg-type]
    discovery = DreetsMetadataDiscovery(activated=True)
    with pytest.raises(DreetsMetadataRefusal) as raised:
        discovery.discover([item()], discovered_on="2026-07-21")  # type: ignore[arg-type]
    assert raised.value.code == "INVALID_DISCOVERY_BATCH"


def test_forbidden_domain_and_pdf_fail_the_whole_discovery():
    discovery = DreetsMetadataDiscovery(activated=True)
    with pytest.raises(DreetsMetadataRefusal) as domain:
        discovery.discover((item(), item(url="https://example.org/item")), discovered_on="2026-07-21")
    assert domain.value.code == "DOMAIN_NOT_ALLOWED"
    with pytest.raises(DreetsMetadataRefusal) as pdf:
        discovery.discover((item(url="https://grand-est.dreets.gouv.fr/file.pdf", mime_type="application/pdf"),), discovered_on="2026-07-21")
    assert pdf.value.code == "PDF_FORBIDDEN"


def test_mime_validation_is_mandatory():
    with pytest.raises(DreetsMetadataRefusal) as raised:
        DreetsMetadataDiscovery(activated=True).discover(
            (item(mime_type="application/json"),), discovered_on="2026-07-21"
        )
    assert raised.value.code == "MIME_NOT_ALLOWED"


def test_quota_and_duplicates_are_refused():
    discovery = DreetsMetadataDiscovery(activated=True, quota=1)
    with pytest.raises(DreetsMetadataRefusal) as quota:
        discovery.discover((item(), item(url="https://grand-est.dreets.gouv.fr/second")), discovered_on="2026-07-21")
    assert quota.value.code == "QUOTA_EXCEEDED"
    with pytest.raises(DreetsMetadataRefusal) as duplicate:
        DreetsMetadataDiscovery(activated=True).discover((item(), item()), discovered_on="2026-07-21")
    assert duplicate.value.code == "DUPLICATE_URL"


def test_no_network_client_download_cache_or_indexing_code_exists():
    import automation.official_knowledge.connectors.dreets_grand_est.dreets_discovery as discovery_module
    import automation.official_knowledge.connectors.dreets_grand_est.dreets_metadata as metadata_module

    sources = inspect.getsource(discovery_module) + inspect.getsource(metadata_module)
    tree = ast.parse(sources)
    imports = {
        alias.name
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not imports & {"requests", "urllib.request", "http.client", "socket", "httpx", "aiohttp"}
    assert "urlopen(" not in sources
    assert "requests.get(" not in sources
    assert not any(token in sources for token in ("write_text(", "write_bytes(", "open(", "index_text("))


def test_discovery_is_deterministic_and_does_not_mutate_input():
    original = item()
    discovery = DreetsMetadataDiscovery(activated=True)
    first = discovery.discover((original,), discovered_on="2026-07-21")
    second = discovery.discover((original,), discovered_on="2026-07-21")
    assert first == second
    assert original == item()


def test_discovered_metadata_is_registered_without_content(tmp_path):
    path = tmp_path / "documents.json"
    registry = build_dreets_document_registry(JsonDocumentStorage(path))
    connector = DreetsGrandEstConnector(metadata_discovery_enabled=True, document_registry=registry)
    changes = connector.register_discovered_metadata((item(),), discovered_on="2026-07-21")
    assert changes[0].kind is ChangeKind.NEW
    stored = registry.find_document(changes[0].document_id)
    assert stored is not None
    assert stored.connector_name == "dreets_grand_est"
    assert stored.title == "Inspection du travail"
    assert not set(stored.to_dict()) & {"text", "content", "html", "pdf", "excerpt"}
    assert "Inspection du travail" in path.read_text(encoding="utf-8")


def test_second_dreets_observation_detects_metadata_update(tmp_path):
    registry = build_dreets_document_registry(JsonDocumentStorage(tmp_path / "documents.json"))
    connector = DreetsGrandEstConnector(metadata_discovery_enabled=True, document_registry=registry)
    first = connector.register_discovered_metadata((item(),), discovered_on="2026-07-21")
    second = connector.register_discovered_metadata((item(title="Inspection du travail mise à jour"),), discovered_on="2026-07-22")
    assert first[0].kind is ChangeKind.NEW
    assert second[0].kind is ChangeKind.TITLE_CHANGED
    assert registry.find_updated_documents() == (second[0].current,)


def test_registry_must_be_explicitly_configured():
    connector = DreetsGrandEstConnector(metadata_discovery_enabled=True)
    with pytest.raises(DreetsMetadataRefusal) as raised:
        connector.register_discovered_metadata((item(),), discovered_on="2026-07-21")
    assert raised.value.code == "REGISTRY_NOT_CONFIGURED"
