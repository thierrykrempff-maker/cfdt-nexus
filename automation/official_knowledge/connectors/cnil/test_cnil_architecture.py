"""Architecture and safety tests for the inert CNIL LOT 0 connector."""

import ast
import unittest
from pathlib import Path

from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_states import ConnectorState
from automation.official_knowledge.document_registry import DocumentRegistry

from .cnil_catalog import (
    CNIL_ALLOWED_DOMAINS,
    CNIL_DOCUMENT_FAMILIES,
    CNIL_PLANNED_CAPABILITIES,
)
from .cnil_connector import CnilConnector
from .cnil_contract import CNIL_DOCUMENT_CONTRACT
from .cnil_models import CnilConnectorParameters, CnilDocumentFamily
from .cnil_platform import CNIL_PLATFORM_CONTRACT, CNIL_REGISTRY, CNIL_VALIDATION


class CnilArchitectureTests(unittest.TestCase):
    def test_connector_platform_integration(self) -> None:
        self.assertIsInstance(CNIL_REGISTRY, ConnectorRegistry)
        self.assertEqual(("cnil",), CNIL_REGISTRY.list_ids())
        self.assertIs(CNIL_PLATFORM_CONTRACT, CNIL_REGISTRY.get("cnil"))
        self.assertTrue(CNIL_VALIDATION.valid)
        self.assertEqual((), CNIL_VALIDATION.errors)

    def test_connector_is_disabled_and_metadata_activable(self) -> None:
        connector = CnilConnector()
        self.assertFalse(connector.enabled)
        self.assertFalse(connector.parameters.enabled)
        self.assertFalse(CNIL_PLATFORM_CONTRACT.enabled)
        self.assertIs(ConnectorState.DISABLED, CNIL_PLATFORM_CONTRACT.state)
        self.assertNotIn("discovery", {item.value for item in CNIL_PLATFORM_CONTRACT.capabilities})
        self.assertNotIn("download", {item.value for item in CNIL_PLATFORM_CONTRACT.capabilities})

    def test_document_contract_is_metadata_only(self) -> None:
        self.assertIs(DocumentPolicy.METADATA_ONLY, CNIL_PLATFORM_CONTRACT.document_policy)
        self.assertEqual("METADATA_ONLY", CNIL_DOCUMENT_CONTRACT.policy)
        self.assertFalse(CNIL_DOCUMENT_CONTRACT.text_indexing_allowed)
        self.assertFalse(CNIL_DOCUMENT_CONTRACT.local_copy_allowed)
        self.assertFalse(CNIL_DOCUMENT_CONTRACT.pdf_allowed)
        self.assertFalse(CNIL_DOCUMENT_CONTRACT.html_extraction_allowed)

    def test_document_contract_requires_provenance_citation_and_https(self) -> None:
        self.assertTrue(CNIL_DOCUMENT_CONTRACT.provenance_required)
        self.assertTrue(CNIL_DOCUMENT_CONTRACT.citation_required)
        self.assertTrue(CNIL_DOCUMENT_CONTRACT.https_required)
        self.assertTrue(CNIL_PLATFORM_CONTRACT.security.network_disabled_by_default)
        self.assertTrue(all(vars(CNIL_PLATFORM_CONTRACT.security).values()))

    def test_only_official_domain_is_declared(self) -> None:
        self.assertEqual(frozenset({"cnil.fr"}), CNIL_ALLOWED_DOMAINS)
        self.assertEqual(("cnil.fr",), CnilConnectorParameters().allowed_domains)

    def test_all_expected_document_families_are_declared(self) -> None:
        self.assertEqual(set(CnilDocumentFamily), set(CNIL_DOCUMENT_FAMILIES))
        self.assertEqual(
            {
                "news", "deliberations", "recommendations", "guides",
                "practical_sheets", "sanctions", "referentials", "faq",
                "other_publications",
            },
            {family.value for family in CNIL_DOCUMENT_FAMILIES},
        )

    def test_planned_capabilities_are_non_operational(self) -> None:
        self.assertEqual(
            {"public_metadata", "metadata_discovery", "document_registry"},
            {capability.name for capability in CNIL_PLANNED_CAPABILITIES},
        )
        self.assertTrue(all(not capability.implemented for capability in CNIL_PLANNED_CAPABILITIES))

    def test_collection_api_is_fail_closed(self) -> None:
        connector = CnilConnector()
        candidate = __import__(
            "automation.official_knowledge.connectors.cnil.cnil_models",
            fromlist=["ResourceCandidate"],
        ).ResourceCandidate("https://www.cnil.fr/fr/synthetic")
        for operation in (
            lambda: connector.discover_resources("synthetic"),
            lambda: connector.fetch_resource(candidate),
        ):
            with self.assertRaises(RuntimeError):
                operation()

    def test_document_registry_compatibility_is_interface_only(self) -> None:
        connector = CnilConnector()
        self.assertTrue(connector.document_registry_compatible)
        self.assertIsNone(connector.document_registry)
        required = {"register_document", "update_document", "find_document"}
        self.assertTrue(required.issubset(set(dir(DocumentRegistry))))

    def test_production_modules_have_no_network_or_persistence_imports(self) -> None:
        forbidden_modules = {"requests", "httpx", "aiohttp", "socket", "urllib.request", "http.client"}
        for path in Path(__file__).parent.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            self.assertTrue(forbidden_modules.isdisjoint(imported), path.name)

    def test_connector_does_not_import_other_connectors(self) -> None:
        root = Path(__file__).parent
        for path in root.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            source = path.read_text(encoding="utf-8").lower()
            for connector in ("dreets", "carsat", "cnil_connector_http", "inrs", "cpam"):
                self.assertNotIn(connector, source, f"{connector} imported by {path.name}")


if __name__ == "__main__":
    unittest.main()
