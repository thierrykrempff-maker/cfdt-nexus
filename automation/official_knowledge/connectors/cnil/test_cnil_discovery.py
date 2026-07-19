"""Offline activation, discovery and Document Registry tests for CNIL LOT 1."""

import ast
import importlib
import unittest
from dataclasses import replace
from pathlib import Path

from automation.official_knowledge.document_registry import ChangeKind, DocumentRecord

from .cnil_connector import CnilConnector, build_cnil_document_registry
from .cnil_discovery import CnilDiscoveryEntry, discover_metadata
from .cnil_metadata import CnilMetadataRefusal


class MemoryStorage:
    def __init__(self) -> None:
        self.documents: tuple[DocumentRecord, ...] = ()

    def load(self) -> tuple[DocumentRecord, ...]:
        return self.documents

    def save(self, documents: tuple[DocumentRecord, ...]) -> None:
        self.documents = documents


def entry(url: str = "https://cnil.fr/fr/actualite-synthetique", **changes) -> CnilDiscoveryEntry:
    values = {
        "url": url,
        "title": "Actualité synthétique",
        "publication_date": "2026-07-01",
        "category": "actualite",
        "family": "actualite",
        "document_type": "actualite",
        "mime_type": "text/html",
        "discovered_at": "2026-07-19",
    }
    values.update(changes)
    return CnilDiscoveryEntry(**values)


class CnilActivationAndDiscoveryTests(unittest.TestCase):
    def test_public_api_is_importable(self) -> None:
        package = importlib.import_module("automation.official_knowledge.connectors.cnil")
        for name in ("CnilConnector", "CnilDiscoveryEntry", "CnilMetadata", "discover_metadata"):
            self.assertTrue(hasattr(package, name), name)

    def test_disabled_by_default(self) -> None:
        connector = CnilConnector()
        self.assertFalse(connector.enabled)
        self.assertEqual("METADATA_ONLY", connector.activation_scope)

    def test_explicit_activation(self) -> None:
        connector = CnilConnector(enabled=True)
        self.assertTrue(connector.enabled)
        self.assertEqual(1, len(connector.discover_metadata((entry(),))))

    def test_activation_is_strictly_boolean(self) -> None:
        for value in (1, "true", None):
            with self.subTest(value=value), self.assertRaises(TypeError):
                CnilConnector(enabled=value)

    def test_non_metadata_mode_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "METADATA_ONLY"):
            CnilConnector(enabled=True, mode="FULL_TEXT")

    def test_disabled_operation_is_refused(self) -> None:
        with self.assertRaisesRegex(CnilMetadataRefusal, "disabled"):
            CnilConnector().discover_metadata((entry(),))

    def test_batch_must_be_tuple(self) -> None:
        with self.assertRaisesRegex(CnilMetadataRefusal, "tuple"):
            discover_metadata([entry()], enabled=True)  # type: ignore[arg-type]

    def test_default_limit_is_fifty(self) -> None:
        batch = tuple(entry(f"https://cnil.fr/fr/item-{index}") for index in range(50))
        self.assertEqual(50, len(discover_metadata(batch, enabled=True)))
        with self.assertRaisesRegex(CnilMetadataRefusal, "exceeded"):
            discover_metadata(batch + (entry("https://cnil.fr/fr/extra"),), enabled=True)

    def test_limit_boundaries_and_invalid_values(self) -> None:
        self.assertEqual((), discover_metadata((), enabled=True, limit=1))
        self.assertEqual((), discover_metadata((), enabled=True, limit=100))
        for value in (0, 101, True, "50"):
            with self.subTest(value=value), self.assertRaises(CnilMetadataRefusal):
                discover_metadata((), enabled=True, limit=value)  # type: ignore[arg-type]

    def test_duplicate_canonical_url_is_refused(self) -> None:
        batch = (entry(), entry("https://www.cnil.fr/fr/actualite-synthetique"))
        with self.assertRaisesRegex(CnilMetadataRefusal, "Duplicate"):
            discover_metadata(batch, enabled=True)

    def test_one_invalid_entry_refuses_whole_batch(self) -> None:
        batch = (entry(), entry("https://evil.example/item"))
        with self.assertRaises(CnilMetadataRefusal):
            discover_metadata(batch, enabled=True)

    def test_output_order_is_deterministic(self) -> None:
        batch = (entry("https://cnil.fr/fr/z"), entry("https://cnil.fr/fr/a"))
        result = discover_metadata(batch, enabled=True)
        self.assertEqual(["https://cnil.fr/fr/a", "https://cnil.fr/fr/z"], [item.canonical_url for item in result])

    def test_entry_and_result_have_no_content_fields(self) -> None:
        forbidden = {"body", "content", "text", "excerpt", "summary", "html", "pdf", "binary", "attachment"}
        self.assertTrue(forbidden.isdisjoint(CnilDiscoveryEntry.__dataclass_fields__))
        self.assertTrue(forbidden.isdisjoint(discover_metadata((entry(),), enabled=True)[0].to_dict()))

    def test_no_network_client_imported(self) -> None:
        forbidden = {"requests", "httpx", "aiohttp", "urllib.request", "http.client", "socket"}
        for path in Path(__file__).parent.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
            self.assertTrue(forbidden.isdisjoint(imports), path.name)


class CnilDocumentRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = MemoryStorage()
        self.registry = build_cnil_document_registry(self.storage)
        self.connector = CnilConnector(registry=self.registry, enabled=True)

    def test_registry_must_be_explicitly_injected(self) -> None:
        with self.assertRaisesRegex(CnilMetadataRefusal, "explicitly"):
            CnilConnector(enabled=True).register_discovered_metadata((entry(),))

    def test_new_publication_and_document_record(self) -> None:
        change = self.connector.register_discovered_metadata((entry(),))[0]
        self.assertIs(ChangeKind.NEW, change.kind)
        self.assertEqual("cnil", change.current.connector_name)
        self.assertEqual("https://cnil.fr/fr/actualite-synthetique", change.current.canonical_url)

    def test_second_pass_without_change(self) -> None:
        self.connector.register_discovered_metadata((entry(),))
        change = self.connector.register_discovered_metadata((entry(discovered_at="2026-07-20"),))[0]
        self.assertIs(ChangeKind.UNCHANGED, change.kind)
        self.assertEqual("2026-07-20", change.current.last_checked)

    def test_title_change(self) -> None:
        self.connector.register_discovered_metadata((entry(),))
        changed = entry(title="Titre modifié", discovered_at="2026-07-20")
        self.assertIs(ChangeKind.TITLE_CHANGED, self.connector.register_discovered_metadata((changed,))[0].kind)

    def test_publication_date_change(self) -> None:
        self.connector.register_discovered_metadata((entry(),))
        changed = entry(publication_date="2026-07-02", discovered_at="2026-07-20")
        self.assertIs(ChangeKind.DATE_CHANGED, self.connector.register_discovered_metadata((changed,))[0].kind)

    def test_category_family_and_type_changes(self) -> None:
        expectations = {
            "category": ChangeKind.CATEGORY_CHANGED,
            "family": ChangeKind.FAMILY_CHANGED,
            "document_type": ChangeKind.DOCUMENT_TYPE_CHANGED,
        }
        for field, kind in expectations.items():
            with self.subTest(field=field):
                storage = MemoryStorage()
                connector = CnilConnector(registry=build_cnil_document_registry(storage), enabled=True)
                connector.register_discovered_metadata((entry(),))
                changed = replace(entry(discovered_at="2026-07-20"), **{field: "guide"})
                self.assertIs(kind, connector.register_discovered_metadata((changed,))[0].kind)

    def test_find_by_connector(self) -> None:
        self.connector.register_discovered_metadata((entry(),))
        self.assertEqual(1, len(self.registry.find_by_connector("cnil")))
        self.assertEqual((), self.registry.find_by_connector("dreets_grand_est"))

    def test_registry_record_contains_no_content(self) -> None:
        record = self.connector.register_discovered_metadata((entry(),))[0].current
        forbidden = {"body", "content", "text", "excerpt", "summary", "html", "pdf", "binary"}
        self.assertTrue(forbidden.isdisjoint(record.to_dict()))
        self.assertTrue(all(isinstance(value, (str, type(None))) for value in record.to_dict().values()))


if __name__ == "__main__":
    unittest.main()
