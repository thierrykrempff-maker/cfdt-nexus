"""Synthetic-only tests for Protection sociale LOT 1C."""
import json,tempfile,unittest
from pathlib import Path
from unittest import mock
from automation.protection_sociale.metadata_confidence import confidence,confidence_level
from automation.protection_sociale.metadata_extractor import extract_metadata,record_id,run_extraction
def source(text=""):
 return {"document_id":"doc-1","source_document_id":"src-1","source_relative_path":"MUTUELLE/NOTICES/synthetic.pdf","source_sha256":"a"*64,"normalized_text":text}
class MetadataExtractorTests(unittest.TestCase):
 def test_assureur_contract_date(self):
  r=extract_metadata(source("Assureur : Organisme Synthétique\nContrat : SYN-001\nDate d'effet : 01/02/2025"));self.assertEqual("Organisme Synthétique",r.metadata["assureur"].value);self.assertEqual("SYN-001",r.metadata["contrat"].value);self.assertEqual("01/02/2025",r.metadata["date_effet"].value)
 def test_type_domain_subdomain_theme(self):
  r=extract_metadata(source("Notice d'information\nGaranties optique optique et dentaire."));self.assertEqual("notice",r.metadata["type_document"].value);self.assertEqual("mutuelle",r.metadata["domaine_principal"].value);self.assertEqual("optique",r.metadata["sous_domaine"].value)
 def test_prevoyance(self):
  r=extract_metadata(source("Incapacité incapacité invalidité décès et maintien de salaire."));self.assertEqual("prévoyance",r.metadata["domaine_principal"].value);self.assertEqual("incapacité",r.metadata["sous_domaine"].value)
 def test_confidence(self):
  self.assertEqual("very_high",confidence("labeled_header")[1]);self.assertEqual("very_low",confidence_level(0.1))
 def test_conflict(self):
  r=extract_metadata(source("Assureur : Alpha Synthétique\nAssureur : Beta Synthétique"));self.assertTrue(r.conflicts);self.assertEqual("extracted_with_conflicts",r.extraction_status)
 def test_absence_not_invented_empty(self):
  r=extract_metadata(source(""));self.assertIsNone(r.metadata["assureur"].value);self.assertEqual("empty",r.extraction_status)
 def test_public(self):
  r=extract_metadata(source("Document destiné aux salariés et aux ayants droit."));self.assertTrue(r.metadata["salariés"].value);self.assertTrue(r.metadata["ayants_droit"].value)
 def test_stable_record_id(self):self.assertEqual(record_id("x"),record_id("x"))
 def test_json_manifests_reports_relative_no_absolute(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1B"/"documents";src.mkdir(parents=True);(src/"x.json").write_text(json.dumps(source("Assureur : Synthétique\nOptique optique")),encoding="utf-8");out=root/"LOT_1C";m=run_extraction(src,out,mode="extract");self.assertEqual(1,m["enriched_count"])
   for rel in ("manifests/metadata_manifest.json","manifests/metadata_summary.md","manifests/metadata_quality_report.json","logs/metadata_conflicts.json","logs/metadata_errors.json"):self.assertTrue((out/rel).exists())
   self.assertNotIn(str(root),"".join(p.read_text(encoding="utf-8") for p in out.rglob("*") if p.is_file()))
 def test_dry_run_no_output(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1B"/"documents";src.mkdir(parents=True);(src/"x.json").write_text(json.dumps(source()),encoding="utf-8");out=root/"LOT_1C";self.assertEqual(1,run_extraction(src,out)["examined_count"]);self.assertFalse(out.exists())
 def test_no_network(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);src=root/"LOT_1B"/"documents";src.mkdir(parents=True);(src/"x.json").write_text(json.dumps(source("Optique")),encoding="utf-8")
   with mock.patch("socket.socket",side_effect=AssertionError("network")):self.assertEqual(1,run_extraction(src,root/"LOT_1C",mode="extract")["enriched_count"])
if __name__=="__main__":unittest.main()
