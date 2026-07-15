"""Synthetic-only tests for the Protection sociale corpus audit."""
import json, tempfile, unittest
from pathlib import Path
from automation.protection_sociale.audit_corpus import audit_corpus, classify_path, sha256_file, write_reports
from automation.protection_sociale.document_models import stable_document_id

class AuditCorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)/"RAW_DOCUMENTS"; self.root.mkdir()
    def tearDown(self): self.temp.cleanup()
    def create(self,relative,content=b"synthetic bytes"):
        p=self.root/relative; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(content); return p
    def test_counts_extensions_empty_duplicates_unknown(self):
        a=self.create("MUTUELLE/NOTICES/a.pdf",b"same"); b=self.create("MUTUELLE/NOTICES/b.PDF",b"same"); self.create("x/empty.txt",b""); self.create("x/data.xyz")
        r=audit_corpus(self.root); self.assertEqual(4,r["total_files"]); self.assertEqual(2,r["extensions"][".pdf"]); self.assertEqual(1,r["empty_file_count"]); self.assertEqual(1,r["duplicate_group_count"]); self.assertEqual([".xyz"],r["unknown_extensions"]); self.assertEqual(sha256_file(a),sha256_file(b))
    def test_classification_domains(self):
        self.assertEqual("mutuelle",classify_path("MUTUELLE/NOTICES/x.pdf")[0]); self.assertEqual("prévoyance",classify_path("PREVOYANCE/INVALIDITE/x.pdf")[0]); self.assertEqual("maintien_salaire",classify_path("PREVOYANCE/MAINTIEN_SALAIRE/x.pdf")[0])
    def test_categories(self):
        self.assertEqual("tableau_garanties",classify_path("MUTUELLE/GARANTIES/tableau.pdf")[1]); self.assertEqual("cotisations",classify_path("MUTUELLE/COTISATIONS/taux.xlsx")[1]); self.assertEqual("formulaire",classify_path("FORMULAIRES/formulaire.docx")[1])
    def test_relative_paths_and_stable_ids(self):
        self.create("PROCEDURES_INTERNES/procedure.pdf"); a=audit_corpus(self.root); b=audit_corpus(self.root)
        self.assertEqual("PROCEDURES_INTERNES/procedure.pdf",a["documents"][0]["source_relative_path"]); self.assertEqual(a["documents"][0]["document_id"],b["documents"][0]["document_id"]); self.assertEqual(stable_document_id("x","y"),stable_document_id("x","y"))
    def test_reports_no_absolute_path_and_source_unchanged(self):
        source=self.create("PREVOYANCE/NOTICES/synthetic.pdf"); before=(source.read_bytes(),source.stat().st_mtime_ns); out=Path(self.temp.name)/"AUDIT"; jp,mp=write_reports(audit_corpus(self.root),out)
        self.assertTrue(jp.is_file() and mp.is_file()); self.assertEqual(before,(source.read_bytes(),source.stat().st_mtime_ns)); self.assertNotIn(str(self.root),jp.read_text(encoding="utf-8")); json.loads(jp.read_text(encoding="utf-8"))
    def test_read_error_is_isolated(self):
        bad=self.create("bad.pdf"); self.create("good.txt")
        def hasher(path):
            if path==bad: raise PermissionError("synthetic")
            return sha256_file(path)
        r=audit_corpus(self.root,hash_function=hasher); self.assertEqual(2,r["total_files"]); self.assertEqual(1,r["unreadable_file_count"])
    def test_personal_hint_uses_name_only(self):
        self.create("COURRIERS/matricule_synthetic.pdf"); r=audit_corpus(self.root); self.assertEqual(1,r["personal_data_hint_count"])
    def test_converter_and_unusual_name(self):
        self.create("PREVOYANCE/ancien.doc"); self.create("MUTUELLE/~$temp.xlsx"); r=audit_corpus(self.root); self.assertEqual([".doc"],r["converter_required_extensions"]); self.assertEqual(1,r["unusual_name_count"])
if __name__=="__main__": unittest.main()
