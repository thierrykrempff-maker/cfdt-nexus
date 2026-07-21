"""Architecture-only and Connector Platform tests for France Chimie."""

import ast
import unittest
from pathlib import Path

from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ErrorCode
from automation.connector_platform.connector_health import HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_states import ConnectorState

from .france_chimie_catalog import (
    FRANCE_CHIMIE_ACCESS_CANDIDATES,
    FRANCE_CHIMIE_ACTIVE_DOMAINS,
    FRANCE_CHIMIE_DOMAIN_CANDIDATES,
    FRANCE_CHIMIE_DOMAIN_STATUS,
)
from .france_chimie_contract import FRANCE_CHIMIE_DOCUMENT_CONTRACT, FranceChimieConnector
from .france_chimie_models import (
    FranceChimieAccessStatus,
    FranceChimieDocumentIdentity,
    FranceChimieDocumentType,
    FranceChimieResourceFamily,
)
from .france_chimie_platform import (
    FRANCE_CHIMIE_NETWORK_NOT_IMPLEMENTED,
    FRANCE_CHIMIE_PLATFORM_CONTRACT,
    FRANCE_CHIMIE_REGISTRY,
    FRANCE_CHIMIE_VALIDATION,
)


class FranceChimieArchitectureTests(unittest.TestCase):
    def identity(self) -> FranceChimieDocumentIdentity:
        return FranceChimieDocumentIdentity(
            reference="SYNTHETIC-001",
            title="Publication synthétique",
            family=FranceChimieResourceFamily.PUBLICATION,
            publication_date="2026-07-21",
            document_type=FranceChimieDocumentType.PUBLICATION,
        )

    def test_platform_contract_is_inactive_metadata_only(self) -> None:
        self.assertIs(ConnectorState.ARCHITECTURE_ONLY, FRANCE_CHIMIE_PLATFORM_CONTRACT.state)
        self.assertFalse(FRANCE_CHIMIE_PLATFORM_CONTRACT.enabled)
        self.assertIs(DocumentPolicy.METADATA_ONLY, FRANCE_CHIMIE_PLATFORM_CONTRACT.document_policy)
        self.assertIs(LicenseId.DOCUMENT_SPECIFIC, FRANCE_CHIMIE_PLATFORM_CONTRACT.license_id)
        self.assertTrue(FRANCE_CHIMIE_VALIDATION.valid)
        self.assertEqual((), FRANCE_CHIMIE_VALIDATION.errors)

    def test_platform_registry_contains_only_france_chimie(self) -> None:
        self.assertIsInstance(FRANCE_CHIMIE_REGISTRY, ConnectorRegistry)
        self.assertEqual(("france_chimie",), FRANCE_CHIMIE_REGISTRY.list_ids())
        self.assertIs(FRANCE_CHIMIE_PLATFORM_CONTRACT, FRANCE_CHIMIE_REGISTRY.get("france_chimie"))

    def test_document_contract_forbids_content_transport_and_scraping(self) -> None:
        contract = FRANCE_CHIMIE_DOCUMENT_CONTRACT
        self.assertEqual("METADATA_ONLY", contract.policy)
        forbidden = (
            contract.cache_allowed,
            contract.text_indexing_allowed,
            contract.local_copy_allowed,
            contract.pdf_storage_allowed,
            contract.html_storage_allowed,
            contract.full_text_allowed,
            contract.download_allowed,
            contract.scraping_allowed,
        )
        self.assertFalse(any(forbidden))
        self.assertTrue(contract.provenance_required)
        self.assertTrue(contract.citation_required)
        self.assertTrue(contract.https_required)

    def test_domain_configuration_is_declared_but_not_active(self) -> None:
        self.assertEqual(("francechimie.fr", "www.francechimie.fr"), FRANCE_CHIMIE_DOMAIN_CANDIDATES)
        self.assertEqual(frozenset(), FRANCE_CHIMIE_ACTIVE_DOMAINS)
        self.assertEqual("pending_official_validation", FRANCE_CHIMIE_DOMAIN_STATUS)
        self.assertTrue(all(item.status is not FranceChimieAccessStatus.NOT_ACTIVATED or item.name == "manual_metadata" for item in FRANCE_CHIMIE_ACCESS_CANDIDATES))

    def test_no_active_connector_capability(self) -> None:
        forbidden = {
            Capability.API,
            Capability.RSS,
            Capability.ATOM,
            Capability.SITEMAP,
            Capability.OPEN_DATA,
            Capability.AUTHENTICATION,
            Capability.CACHE,
            Capability.SYNC,
            Capability.DISCOVERY,
            Capability.SEARCH,
            Capability.DOWNLOAD,
            Capability.VERSIONING,
        }
        self.assertTrue(forbidden.isdisjoint(FRANCE_CHIMIE_PLATFORM_CONTRACT.capabilities))

    def test_facade_is_disabled_and_registry_compatible(self) -> None:
        connector = FranceChimieConnector()
        self.assertFalse(connector.enabled)
        self.assertEqual("architecture_only", connector.connector_status)
        self.assertTrue(connector.document_registry_compatible)
        self.assertIsNone(connector.document_registry)
        self.assertIs(HealthStatus.DISABLED, connector.health.status)
        self.assertEqual((0, 0, 0), (connector.statistics.document_count, connector.statistics.consultation_count, connector.statistics.average_duration_ms))

    def test_identity_round_trip_and_platform_conversions(self) -> None:
        connector = FranceChimieConnector()
        identity = self.identity()
        self.assertEqual(identity, connector.deserialize_identity(connector.serialize_identity(identity)))
        self.assertEqual(identity.fingerprint(), identity.fingerprint())
        self.assertIs(DocumentPolicy.METADATA_ONLY, identity.platform_policy())
        self.assertIs(LicenseId.DOCUMENT_SPECIFIC, identity.platform_license())
        self.assertEqual("France Chimie", identity.citation("https://example.invalid/publication").author)
        self.assertEqual("france_chimie", identity.provenance("https://example.invalid/publication").source_id)

    def test_network_operations_fail_closed(self) -> None:
        connector = FranceChimieConnector()
        calls = (
            lambda: connector.discover("synthetic"),
            lambda: connector.fetch(self.identity()),
            connector.synchronize,
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaisesRegex(RuntimeError, FRANCE_CHIMIE_NETWORK_NOT_IMPLEMENTED) as raised:
                    call()
                self.assertIs(ErrorCode.NETWORK_DISABLED, raised.exception.code)

    def test_network_is_disabled_by_default(self) -> None:
        self.assertEqual("NETWORK_DISABLED_BY_DEFAULT", NETWORK_DISABLED_BY_DEFAULT)
        self.assertTrue(FRANCE_CHIMIE_PLATFORM_CONTRACT.security.network_disabled_by_default)

    def test_production_modules_have_no_network_or_scraping_import(self) -> None:
        forbidden = {"requests", "httpx", "aiohttp", "urllib", "urllib.request", "http.client", "socket", "bs4", "scrapy"}
        root = Path(__file__).parent
        for path in root.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
            self.assertTrue(forbidden.isdisjoint(imports), path.name)


if __name__ == "__main__":
    unittest.main()
