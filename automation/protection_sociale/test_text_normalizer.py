"""Synthetic-only tests for Protection sociale LOT 1B."""
import json,tempfile,unittest
from pathlib import Path
from unittest import mock
from automation.protection_sociale.text_normalizer import normalize_document,normalize_text,normalized_id,run_normalization
from automation.protection_sociale.text_quality import assess_quality,quality_level
def source(text="Texte   synthétique.\r\n--- PAGE 1 ---\r\nSuite utile."):
 return {"document_id":"source-1","source_relative_path":"synthetic/test.pdf","source_sha256":"a"*64,"extraction_status":"extracted","text_content":text,"page_count":1,"paragraph_count":None,"table_count":None,"warnings":[]}
class TextNormalizerTests(unittest.TestCase):
 def test_normalization_preserves_useful_text(self):
  text="A   B\r\nC";n,c=normalize_text(text);self.assertEqual("A B\nC",n);self.assertIn("horizontal_spaces_normalized",c)
 def test_separators_preserved(self):
  text="--- PAGE 1 ---\n--- PARAGRAPH 2 ---\n--- TABLE 1 ---";self.assertEqual(text,normalize_text(text)[0])
 def test_control_removed_special_preserved(self):
  n,_=normalize_text("é €\x00 utile");self.assertEqual("é € utile",n)
 def test_empty_quality(self):
  r=normalize_document(source(""));self.assertEqual("empty",r.normalization_status);self.assertEqual(0,r.quality_score);self.assertEqual("unusable",r.quality_level)
 def test_quality_levels(self):
  self.assertEqual("excellent",quality_level(95));self.assertEqual("good",quality_level(80));self.assertEqual("acceptable",quality_level(60));self.assertEqual("poor",quality_level(30));self.assertEqual("unusable",quality_level(10))
 def test_quality_flags(self):
  self.assertIn("very_short_text",assess_quality("court",source("court"))["flags"])
 def test_stable_id(self):self.assertEqual(normalized_id("x"),normalized_id("x"))
 def test_reports_sources_unchanged_and_no_absolute_paths(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1A"/"documents";out=root/"LOT_1B";src.mkdir(parents=True);p=src/"x.json";p.write_text(json.dumps(source()),encoding="utf-8");before=p.read_bytes();m=run_normalization(src,out,mode="normalize");self.assertEqual(1,m["normalized_count"]);self.assertEqual(before,p.read_bytes())
   for rel in ("manifests/normalization_manifest.json","manifests/normalization_summary.md","manifests/quality_report.json","logs/normalization_errors.json"):self.assertTrue((out/rel).exists())
   self.assertNotIn(str(root),"".join(x.read_text(encoding="utf-8") for x in out.rglob("*") if x.is_file()))
 def test_dry_run_no_output(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1A"/"documents";src.mkdir(parents=True);(src/"x.json").write_text(json.dumps(source()),encoding="utf-8");out=root/"LOT_1B";self.assertEqual(1,run_normalization(src,out)["examined_count"]);self.assertFalse(out.exists())
 def test_resume_force(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1A"/"documents";src.mkdir(parents=True);(src/"x.json").write_text(json.dumps(source()),encoding="utf-8");out=root/"LOT_1B";run_normalization(src,out,mode="normalize");self.assertEqual(1,run_normalization(src,out,mode="normalize")["resumed_count"]);self.assertEqual(1,run_normalization(src,out,mode="normalize",force=True)["normalized_count"])
 def test_no_network(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1A"/"documents";src.mkdir(parents=True);(src/"x.json").write_text(json.dumps(source()),encoding="utf-8")
   with mock.patch("socket.socket",side_effect=AssertionError("network")):self.assertEqual(1,run_normalization(src,root/"LOT_1B",mode="normalize")["normalized_count"])
if __name__=="__main__":unittest.main()
