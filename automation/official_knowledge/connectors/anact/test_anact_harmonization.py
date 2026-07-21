"""LOT 1 tests for the harmonized, offline ANACT foundation."""

import subprocess
import sys
import unittest
from datetime import datetime, timezone

from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_states import ConnectorState
from automation.official_knowledge.document_registry import (
    DocumentRecord,
    DocumentValidator,
    stable_document_id,
)

from . import ANACT_NETWORK_NOT_IMPLEMENTED, AnactConnector, AnactResource
from .anact_models import (
    AnactResourceType,
    AnactTheme,
    ConfidenceLevel,
    GeographicScope,
    ValidationStatus,
)


class AnactHarmonizationTests(unittest.TestCase):
    def resource(self, url: str = "https://example.invalid/anact/synthetic") -> AnactResource:
        return AnactResource(
            "ANACT-SYNTHETIC-001",
            "anact_national",
            AnactResourceType.GUIDE,
            AnactTheme.QVCT,
            "Synthetic ANACT metadata",
            url,
            collected_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
            scope=GeographicScope.NATIONAL,
            validation_status=ValidationStatus.PENDING,
            confidence=ConfidenceLevel.LOW,
            synthetic_only=True,
            official_content=False,
        )

    def test_common_stable_document_identity(self) -> None:
        resource = self.resource()
        self.assertEqual(stable_document_id("anact", resource.canonical_url), resource.document_id)
        self.assertNotEqual(resource.resource_id, resource.document_id)

    def test_identity_is_stable_for_one_canonical_url(self) -> None:
        self.assertEqual(self.resource().document_id, self.resource().document_id)

    def test_identity_differs_for_distinct_canonical_urls(self) -> None:
        self.assertNotEqual(
            self.resource("https://example.invalid/anact/a").document_id,
            self.resource("https://example.invalid/anact/b").document_id,
        )

    def test_resource_builds_valid_public_registry_record(self) -> None:
        record = self.resource().to_document_record(checked_on="2026-07-21")
        self.assertIsInstance(record, DocumentRecord)
        self.assertEqual("anact", record.connector_name)
        self.assertEqual(self.resource().document_id, record.document_id)
        DocumentValidator({"anact": frozenset({"example.invalid"})}).validate_new(record)

    def test_connector_accepts_explicit_registry_injection(self) -> None:
        registry_port = object()
        connector = AnactConnector(document_registry=registry_port)
        self.assertIs(registry_port, connector.document_registry)
        self.assertTrue(connector.document_registry_compatible)

    def test_platform_remains_inactive_metadata_only(self) -> None:
        connector = AnactConnector()
        self.assertIs(ConnectorState.ARCHITECTURE_ONLY, connector.platform_contract.state)
        self.assertFalse(connector.enabled)
        self.assertIs(DocumentPolicy.METADATA_ONLY, connector.platform_contract.document_policy)
        self.assertEqual("METADATA_ONLY", connector.document_contract.policy)

    def test_content_storage_is_forbidden(self) -> None:
        contract = AnactConnector.document_contract
        self.assertFalse(
            any(
                (
                    contract.cache_allowed,
                    contract.text_indexing_allowed,
                    contract.local_copy_allowed,
                    contract.pdf_storage_allowed,
                    contract.html_storage_allowed,
                    contract.full_text_allowed,
                    contract.download_allowed,
                    contract.scraping_allowed,
                )
            )
        )
        self.assertIsNone(getattr(self.resource(), "fulltext", None))

    def test_public_import_does_not_load_http_transports(self) -> None:
        code = (
            "import sys; "
            "import automation.official_knowledge.connectors.anact as package; "
            "assert package.AnactConnector; "
            "assert 'automation.official_knowledge.connectors.anact.anact_sitemap_transport' not in sys.modules; "
            "assert 'automation.official_knowledge.connectors.anact.anact_page_metadata_transport' not in sys.modules"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_historical_public_imports_remain_available(self) -> None:
        self.assertEqual("ANACT_CONNECTOR_NETWORK_NOT_IMPLEMENTED", ANACT_NETWORK_NOT_IMPLEMENTED)
        self.assertEqual("anact", AnactConnector.connector_id)
        self.assertIsNotNone(AnactResource)


if __name__ == "__main__":
    unittest.main()
