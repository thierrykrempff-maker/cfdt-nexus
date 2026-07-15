"""Synthetic-only tests for Protection sociale LOT 1D."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from automation.protection_sociale.chunk_builder import build_document, run
from automation.protection_sociale.chunk_quality import validate_coverage
from automation.protection_sociale.chunk_rules import ChunkConfig, estimate_tokens


def document(text: str = "Phrase synthétique. " * 100, quality: str = "excellent", **extra):
    value = {"document_id": "doc-1", "source_document_id": "src-1", "source_relative_path": "MUTUELLE/synthetic.pdf",
             "source_sha256": "a" * 64, "normalization_status": "normalized", "normalized_text": text,
             "quality_level": quality, "table_count": 0}
    value.update(extra); return value


def metadata():
    def item(value, confidence="high"): return {"value": value, "confidence_level": confidence}
    return {"metadata_record_id": "meta-1", "document_id": "doc-1", "metadata_quality_level": "good",
            "metadata": {"domaine_principal": item("mutuelle"), "sous_domaine": item("optique"),
                         "type_document": item("notice"), "organisme_émetteur": item(None, "very_low"),
                         "assureur": item("Synthétique Assurance"), "contrat": item("SYN-1"),
                         "référence": item(None, "very_low"), "date_effet": item("01/01/2025"),
                         "date_fin": item(None, "very_low"), "public_concerné": item(["salariés"]),
                         "thème_principal": item("optique")}}


class ChunkBuilderTests(unittest.TestCase):
    config = ChunkConfig(180, 300, 30, 25)

    def test_stable_ids_and_order(self):
        first, _ = build_document(document(), metadata(), self.config, "fixed")
        second, _ = build_document(document(), metadata(), self.config, "other")
        self.assertEqual([c["chunk_id"] for c in first], [c["chunk_id"] for c in second])
        self.assertEqual(list(range(len(first))), [c["chunk_index"] for c in first])

    def test_small_paragraphs_grouped_and_target_configurable(self):
        text = "Petit paragraphe.\n\n" * 5
        chunks, _ = build_document(document(text), metadata(), ChunkConfig(200, 240, 20, 10))
        self.assertEqual(1, len(chunks))
        smaller, _ = build_document(document(text), metadata(), ChunkConfig(40, 70, 10, 5))
        self.assertGreater(len(smaller), 1)

    def test_large_block_maximum_strict_cut_and_complete_coverage(self):
        chunks, summary = build_document(document("x" * 1000), metadata(), ChunkConfig(80, 100, 10, 10))
        self.assertTrue(all(c["text_length_chars"] <= 100 for c in chunks))
        self.assertTrue(any("strict_cut" in c["quality_flags"] for c in chunks))
        self.assertTrue(summary["coverage"]["reconstruction_ok"])

    def test_overlap_first_last_and_links(self):
        chunks, _ = build_document(document(), metadata(), self.config)
        self.assertEqual(0, chunks[0]["overlap_previous_chars"])
        self.assertIsNone(chunks[0]["previous_chunk_id"]); self.assertIsNone(chunks[-1]["next_chunk_id"])
        self.assertEqual(chunks[0]["next_chunk_id"], chunks[1]["chunk_id"])
        self.assertGreater(chunks[1]["overlap_previous_chars"], 0)

    def test_page_and_paragraph_locators(self):
        text = "--- PAGE 1 ---\nTexte synthétique.\n\nParagraphe.\n--- PAGE 2 ---\nSuite."
        chunks, _ = build_document(document(text), metadata(), ChunkConfig(200, 250, 10, 10))
        self.assertEqual([1, 2], chunks[0]["page_numbers"])
        self.assertTrue(chunks[0]["paragraph_indexes"]); self.assertTrue(chunks[0]["source_section_ids"])

    def test_table_and_flattened_table(self):
        marked, _ = build_document(document("--- TABLE 1 ---\nLigne synthétique"), metadata(), ChunkConfig())
        self.assertEqual("table", marked[0]["chunk_type"])
        flat, _ = build_document(document("Ligne aplatie", table_count=1), metadata(), ChunkConfig())
        self.assertIn("flattened_table", flat[0]["quality_flags"])

    def test_text_type_and_local_token_estimate(self):
        chunks, _ = build_document(document("abcdefghij"), metadata(), ChunkConfig())
        self.assertEqual("text", chunks[0]["chunk_type"]); self.assertEqual(3, estimate_tokens("abcdefghij"))

    def test_empty_placeholder_and_unusable_source(self):
        chunks, summary = build_document(document("", "unusable"), None, ChunkConfig())
        self.assertEqual("empty_placeholder", chunks[0]["chunk_type"]); self.assertFalse(chunks[0]["is_indexable"])
        self.assertEqual("empty_or_unusable_source", chunks[0]["non_indexable_reason"]); self.assertEqual(0, summary["indexable_chunk_count"])
        chunks, _ = build_document(document("Texte", "unusable"), metadata(), ChunkConfig())
        self.assertFalse(chunks[0]["is_indexable"])

    def test_metadata_and_topic_tags_attached_without_invention(self):
        chunks, _ = build_document(document("Texte"), metadata(), ChunkConfig())
        snap = chunks[0]["metadata_snapshot"]
        self.assertEqual("mutuelle", snap["domaine_principal"]["value"]); self.assertEqual(["optique"], snap["topic_tags"]["value"])
        chunks, _ = build_document(document("Texte"), None, ChunkConfig())
        self.assertIsNone(chunks[0]["metadata_snapshot"]["assureur"]["value"]); self.assertEqual([], chunks[0]["metadata_snapshot"]["topic_tags"]["value"])

    def test_quality_deterministic_short_and_excessive_overlap(self):
        chunks, _ = build_document(document("court"), metadata(), ChunkConfig(100, 120, 30, 5), "fixed")
        self.assertIn("chunk_too_short", chunks[0]["quality_flags"])
        self.assertEqual(chunks[0]["chunk_quality_score"], deepcopy(chunks)[0]["chunk_quality_score"])

    def test_artificial_loss_and_reconstruction_order(self):
        bad = validate_coverage("abcdef", [(0, 3), (4, 6)])
        self.assertFalse(bad["reconstruction_ok"]); self.assertTrue(bad["losses_detected"])
        good = validate_coverage("abcdef", [(0, 3), (3, 6)])
        self.assertTrue(good["reconstruction_ok"])

    def test_duplicates_preserved_and_source_unchanged(self):
        source = document("Même texte", duplicate_group_id="dup-1", content_id="content-1")
        before = json.dumps(source, sort_keys=True); first, _ = build_document(source, metadata(), ChunkConfig())
        second = dict(source, document_id="doc-2", source_relative_path="AUTRE/synthetic.pdf")
        other, _ = build_document(second, metadata(), ChunkConfig())
        self.assertNotEqual(first[0]["chunk_id"], other[0]["chunk_id"]); self.assertEqual("dup-1", first[0]["duplicate_group_id"])
        self.assertEqual(before, json.dumps(source, sort_keys=True))

    def test_relative_path_and_absolute_path_refused(self):
        chunks, _ = build_document(document("Texte"), metadata(), ChunkConfig())
        self.assertFalse(Path(chunks[0]["source_relative_path"]).is_absolute())
        with self.assertRaises(ValueError): build_document(document("Texte", source_relative_path="C:/secret/doc.pdf"), metadata(), ChunkConfig())

    def test_build_reports_resume_force_filters_and_isolated_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); normalized = root / "LOT_1B" / "documents"; meta = root / "metadata"; output = root / "LOT_1D"
            normalized.mkdir(parents=True); meta.mkdir()
            (normalized / "good.json").write_text(json.dumps(document()), encoding="utf-8")
            (normalized / "bad.json").write_text("{", encoding="utf-8")
            (meta / "record.json").write_text(json.dumps(metadata()), encoding="utf-8")
            stats = run(normalized, meta, output, ChunkConfig(), "build")
            self.assertEqual(1, stats["errors"])
            for name in ("chunk_manifest.json", "chunk_summary.md", "chunk_quality_report.json", "chunk_coverage_report.json"):
                self.assertTrue((output / "manifests" / name).exists())
            self.assertTrue((output / "logs" / "chunk_errors.json").exists())
            self.assertEqual(1, run(normalized, meta, output, ChunkConfig(), "build")["documents_resumed"])
            self.assertEqual(0, run(normalized, meta, output, ChunkConfig(), "build", force=True)["documents_resumed"])
            self.assertEqual(1, run(normalized, meta, output, ChunkConfig(), filters={"domain": "mutuelle"})["documents_chunked"])
            self.assertEqual(0, run(normalized, meta, output, ChunkConfig(), filters={"domain": "prévoyance"})["documents_chunked"])

    def test_guards_raw_and_prior_lots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); raw = root / "RAW_DOCUMENTS"; meta = root / "metadata"; source = root / "source"
            raw.mkdir(); meta.mkdir(); source.mkdir()
            with self.assertRaises(ValueError): run(raw, meta, root / "LOT_1D", ChunkConfig())
            for unsafe in ("LOT_1A", "LOT_1B", "LOT_1C"):
                with self.assertRaises(ValueError): run(source, meta, root / unsafe, ChunkConfig())

    def test_no_network_call(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")):
            build_document(document("Texte synthétique"), metadata(), ChunkConfig())


if __name__ == "__main__":
    unittest.main()
