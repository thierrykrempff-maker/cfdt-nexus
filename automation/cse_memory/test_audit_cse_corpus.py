import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation.cse_memory.audit_cse_corpus import (
    audit_corpus,
    detect_family,
    detect_years,
    sha256_file,
    write_reports,
)


class AuditCseCorpusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "RAW_DOCUMENTS"
        self.root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def create(self, relative, content=b"synthetic test data"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_counts_extensions_empty_unknown_and_duplicates(self):
        first = self.create("PV_CSE/2024/meeting.pdf", b"same")
        second = self.create("PV_CSE/2024/copy.PDF", b"same")
        self.create("notes/empty.txt", b"")
        self.create("misc/data.xyz", b"unknown")
        report = audit_corpus(self.root)
        self.assertEqual(report["total_files"], 4)
        self.assertEqual(report["extensions"][".pdf"], 2)
        self.assertEqual(report["empty_file_count"], 1)
        self.assertEqual(report["unknown_extensions"], [".xyz"])
        self.assertEqual(report["duplicate_group_count"], 1)
        self.assertEqual(sha256_file(first), sha256_file(second))

    def test_year_and_family_detection(self):
        self.assertEqual(detect_years("archives/2021/PV.pdf"), ["2021"])
        self.assertEqual(detect_family("PV_CSE/2021/PV du CSE.pdf"), "PV CSE")
        self.assertEqual(detect_family("archives/CHSCT/reunion.pdf"), "CHSCT")
        self.assertEqual(detect_family("consultations/projet.pdf"), "consultations")

    def test_reports_are_generated_with_relative_paths(self):
        self.create("annexes/example.docx")
        report = audit_corpus(self.root)
        output = Path(self.temporary.name) / "AUDIT"
        json_path, markdown_path = write_reports(report, output)
        self.assertTrue(json_path.is_file())
        self.assertTrue(markdown_path.is_file())
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertIn("annexes/example.docx", loaded["supported_files"])
        self.assertNotIn(str(self.root), json_path.read_text(encoding="utf-8"))

    def test_source_files_are_not_modified(self):
        source = self.create("NAO/2023/source.xlsx", b"immutable synthetic bytes")
        before = (source.read_bytes(), source.stat().st_mtime_ns)
        audit_corpus(self.root)
        after = (source.read_bytes(), source.stat().st_mtime_ns)
        self.assertEqual(before, after)

    def test_read_error_does_not_stop_audit(self):
        bad = self.create("bad.pdf", b"unreadable synthetic file")
        good = self.create("good.txt", b"readable synthetic file")

        def selective_hash(path):
            if path == bad:
                raise PermissionError("synthetic denial")
            return sha256_file(path)

        report = audit_corpus(self.root, hash_function=selective_hash)
        self.assertEqual(report["total_files"], 2)
        self.assertEqual(report["unreadable_file_count"], 1)
        self.assertEqual(report["unreadable_files"][0]["path"], "bad.pdf")
        self.assertIn("good.txt", report["supported_files"])


if __name__ == "__main__":
    unittest.main()
