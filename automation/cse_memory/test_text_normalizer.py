import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.cse_memory import text_normalizer as normalizer
from automation.cse_memory.text_quality import assess_quality


def synthetic_record(document_id="synthetic-source", text="Synthetic normalized text " * 20, **overrides):
    record = {
        "document_id": document_id,
        "source_relative_path": "synthetic/2024/document.pdf",
        "source_extension": ".pdf",
        "source_sha256": "a" * 64,
        "source_size_bytes": 2048,
        "extraction_status": "extracted",
        "text_content": text,
        "text_length": len(text),
        "page_count": 1,
        "slide_count": None,
        "sheet_count": None,
        "warnings": [],
    }
    record.update(overrides)
    return record


class TextNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.source = self.base / "PROCESSED" / "LOT_1A" / "documents"
        self.output = self.base / "PROCESSED" / "LOT_1B"
        self.source.mkdir(parents=True)

    def tearDown(self):
        self.temporary.cleanup()

    def save_record(self, name="source.json", **values):
        record = synthetic_record(**values)
        path = self.source / name
        path.write_text(json.dumps(record), encoding="utf-8")
        return path, record

    def test_line_endings_spaces_blank_lines_and_controls(self):
        text = "First\r\nline   with\tspaces\x00\r\n\r\n\r\nSecond"
        result, changes = normalizer.normalize_text(text)
        self.assertEqual(result, "First\nline with spaces\n\nSecond")
        self.assertIn("line_endings_normalized", changes)
        self.assertIn("control_characters_removed", changes)
        self.assertIn("horizontal_spaces_normalized", changes)
        self.assertIn("excessive_blank_lines_reduced", changes)

    def test_quotes_apostrophes_dashes_and_punctuation(self):
        result, changes = normalizer.normalize_text("« Texte » l ’ accord — suite ,ok")
        self.assertEqual(result, '" Texte " l\'accord - suite, ok')
        self.assertIn("typographic_quotes_and_dashes_normalized", changes)
        self.assertIn("unambiguous_punctuation_spacing_normalized", changes)

    def test_probable_hyphenation_and_compound_word(self):
        result, _ = normalizer.normalize_text("La normali-\nsation reste temps-partiel.")
        self.assertIn("normalisation", result)
        self.assertIn("temps-partiel", result)

    def test_dates_numbers_acronyms_references_and_accents_are_preserved(self):
        text = "CSE 24/06/2024 : 12,5 % - référence AB-123 Égalité"
        result, _ = normalizer.normalize_text(text)
        for value in ("CSE", "24/06/2024", "12,5%", "AB-123", "Égalité"):
            self.assertIn(value, result)

    def test_page_separators_and_blocks_are_preserved(self):
        text = "--- PAGE 1 ---\nTITLE:\n\n- item\n\n--- PAGE 2 ---\nA\tB"
        normalized, _ = normalizer.normalize_text(text)
        blocks = normalizer.generate_blocks(normalized, "doc")
        self.assertEqual(sum(block.block_type == "separator" for block in blocks), 2)
        self.assertTrue(any(block.block_type == "heading_candidate" for block in blocks))
        self.assertTrue(any(block.source_locator == "page 2" for block in blocks))

    def test_empty_document_is_unusable(self):
        document = normalizer.normalize_document(synthetic_record(text=""))
        self.assertEqual(document.normalization_status, "empty")
        self.assertEqual(document.quality_score, 0)
        self.assertEqual(document.quality_level, "unusable")

    def test_quality_excellent_and_poor(self):
        excellent = assess_quality("This is a coherent synthetic sentence. " * 30, synthetic_record(), 10)
        poor = assess_quality("!\n!\n!\n!\n!\n!\n!\n!\n", synthetic_record(), 1)
        self.assertEqual(excellent["level"], "excellent")
        self.assertIn(poor["level"], {"poor", "unusable"})

    def test_abnormal_repetition_is_flagged(self):
        text = "\n".join(["Repeated synthetic line"] * 20 + ["Other line"])
        quality = assess_quality(text, synthetic_record(), 3)
        self.assertIn("abnormal_repetition", quality["flags"])

    def test_pages_without_text_and_probable_image_pdf(self):
        source = synthetic_record(page_count=4, warnings=[f"page_without_text:{i}" for i in range(1, 5)])
        quality = assess_quality("Small extracted fragment " * 10, source, 2)
        self.assertIn("pages_without_text", quality["flags"])
        self.assertIn("probable_image_pdf_without_ocr", quality["flags"])

    def test_repeated_headers_require_high_confidence(self):
        text = "\n".join(
            f"--- PAGE {index} ---\nSynthetic Header\nBody unique {index}\nSynthetic Footer"
            for index in range(1, 5)
        )
        candidates = normalizer.repeated_header_footer_candidates(text)
        self.assertEqual(candidates, {"Synthetic Header", "Synthetic Footer"})
        cleaned, removed = normalizer.remove_repeated_lines(text, candidates)
        self.assertNotIn("Synthetic Header", cleaned)
        self.assertEqual(set(removed), candidates)

    def test_insufficient_repetition_is_not_removed(self):
        text = "--- PAGE 1 ---\nHeader\nBody\n--- PAGE 2 ---\nHeader\nOther"
        self.assertEqual(normalizer.repeated_header_footer_candidates(text), set())

    def test_document_id_is_deterministic_and_linked(self):
        first = normalizer.normalize_document(synthetic_record())
        second = normalizer.normalize_document(synthetic_record())
        self.assertEqual(first.document_id, second.document_id)
        self.assertEqual(first.source_document_id, "synthetic-source")

    def test_resume_and_force(self):
        self.save_record()
        first = normalizer.run_normalization(self.source, self.output, mode="normalize")
        second = normalizer.run_normalization(self.source, self.output, mode="normalize")
        forced = normalizer.run_normalization(self.source, self.output, mode="normalize", force=True)
        self.assertEqual(first["normalized_count"], 1)
        self.assertEqual(second["resumed_count"], 1)
        self.assertEqual(forced["normalized_count"], 1)

    def test_path_guards(self):
        raw = self.base / "RAW_DOCUMENTS"
        raw.mkdir()
        with self.assertRaises(ValueError):
            normalizer.run_normalization(raw, self.output)
        with self.assertRaises(ValueError):
            normalizer.run_normalization(self.source, self.base / "PROCESSED" / "LOT_1A" / "output")

    def test_source_json_is_not_modified_and_outputs_have_no_absolute_path(self):
        path, _ = self.save_record(text="Synthetic C:\\Users\\Example\\secret text " * 10)
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        normalizer.run_normalization(self.source, self.output, mode="normalize")
        after = (path.read_bytes(), path.stat().st_mtime_ns)
        self.assertEqual(before, after)
        for output in self.output.rglob("*"):
            if output.is_file():
                self.assertNotIn("C:\\Users", output.read_text(encoding="utf-8"))

    def test_error_isolated_and_reports_generated(self):
        self.save_record("bad.json", document_id="bad")
        self.save_record("good.json", document_id="good")
        original = normalizer.normalize_document

        def selective(record, **kwargs):
            if record["document_id"] == "bad":
                raise RuntimeError("synthetic failure")
            return original(record, **kwargs)

        with mock.patch.object(normalizer, "normalize_document", side_effect=selective):
            result = normalizer.run_normalization(self.source, self.output, mode="normalize")
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["normalized_count"], 1)
        self.assertTrue((self.output / "manifests" / "normalization_manifest.json").is_file())
        self.assertTrue((self.output / "manifests" / "normalization_summary.md").is_file())
        self.assertTrue((self.output / "manifests" / "quality_report.json").is_file())
        self.assertTrue((self.output / "logs" / "normalization_errors.json").is_file())

    def test_dry_run_filters_limit_and_writes_nothing(self):
        self.save_record("one.json", document_id="one")
        self.save_record("two.json", document_id="two", source_extension=".docx")
        result = normalizer.run_normalization(
            self.source, self.output, mode="dry-run", extensions={"pdf"}, limit=1,
        )
        self.assertEqual(result["examined_count"], 1)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
