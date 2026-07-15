import json,tempfile,unittest
from pathlib import Path
from automation.cse_memory.metadata_rules import date_candidates,categorical_candidates,INSTANCE_PATTERNS,MEETING_PATTERNS,KIND_PATTERNS,STATUS_PATTERNS,number_candidates
from automation.cse_memory.metadata_confidence import arbitrate
from automation.cse_memory.metadata_extractor import extract_metadata,run,record_id

def doc(text="--- PAGE 1 ---\nPV CSE du 21 mars 2024",path="PV_CSE/2024/PV CSE 21.03.2024.pdf",id="d"):
 return {"document_id":id,"source_document_id":"s","source_relative_path":path,"source_sha256":"a"*64,"normalized_text":text,"blocks":[{"block_type":"separator","text":"--- PAGE 1 ---"},{"block_type":"heading_candidate","text":text.splitlines()[-1]}],"quality_level":"good","detected_language_hint":"fr"}
class Tests(unittest.TestCase):
 def test_dates(self):
  for value in ("21 mars 2024","21/03/2024","2024-03-21"):self.assertEqual(date_candidates(value,"first_block")[0]["value"],"2024-03-21")
  self.assertEqual(date_candidates("31/02/2024","first_block"),[])
 def test_priority_agreement_alternatives_conflict(self):
  c=date_candidates("21 mars 2024","first_block")+date_candidates("22.03.2024.pdf","filename");v=arbitrate(c,"missing");self.assertEqual(v.value,"2024-03-21");self.assertTrue(v.alternatives)
  agree=arbitrate(date_candidates("21 mars 2024","first_block")+date_candidates("21.03.2024","filename"),"missing");self.assertGreaterEqual(agree.confidence,.9)
 def test_instances_and_meetings(self):
  for value in ("CSE","CE","CHSCT","CSSCT"):
   got=arbitrate(categorical_candidates([("first_block",value)],INSTANCE_PATTERNS,"I"),"m");self.assertEqual(got.value,value)
  self.assertEqual(arbitrate(categorical_candidates([("first_block","réunion extraordinaire")],MEETING_PATTERNS,"M"),"m").value,"extraordinaire")
  self.assertIsNone(arbitrate(categorical_candidates([("first_block","réunion")],MEETING_PATTERNS,"M"),"m").value)
 def test_kinds_status_number(self):
  self.assertEqual(arbitrate(categorical_candidates([("filename","projet de PV")],KIND_PATTERNS,"K"),"m").value,"projet de proces-verbal")
  self.assertEqual(arbitrate(categorical_candidates([("filename","ordre du jour convocation")],KIND_PATTERNS,"K"),"m").value,"ordre du jour")
  self.assertEqual(arbitrate(categorical_candidates([("first_block","version définitive")],STATUS_PATTERNS,"S"),"m").value,"final")
  self.assertEqual(arbitrate(number_candidates([("first_block","PV n° 12")]),"m").value,"12")
  self.assertEqual(number_candidates([("first_block","page 12")]),[])
 def test_record_and_quarter(self):
  r=extract_metadata(doc());self.assertEqual(r.metadata["quarter"].value,1);self.assertEqual(r.metadata["instance"].value,"CSE");self.assertEqual(r.metadata_record_id,record_id("d"))
 def test_missing_null(self): self.assertIsNone(extract_metadata(doc("texte sans indice","folder/file.bin")).metadata["meeting_date"].value)
 def test_explicit_conflicts(self):
  r=extract_metadata(doc("--- PAGE 1 ---\nOrdre du jour CE du 21 mars 2024 projet définitif","PV_CSE/2054/PV CSE 22.03.2023.pdf"));types={c["type"] for c in r.conflicts};self.assertIn("suspicious_path_year",types);self.assertIn("filename_text_year_mismatch",types);self.assertIn("path_text_instance_mismatch",types);self.assertIn("draft_and_final_status",types)
 def test_pipeline_resume_reports_guards_and_immutability(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);src=base/"PROCESSED"/"LOT_1B"/"documents";out=base/"PROCESSED"/"LOT_1C";src.mkdir(parents=True);p=src/"d.json";p.write_text(json.dumps(doc()),encoding="utf-8");before=p.read_bytes();self.assertEqual(run(src,out,"extract")["enriched_count"],1);self.assertEqual(run(src,out,"extract")["resumed_count"],1);self.assertEqual(run(src,out,"extract",force=True)["enriched_count"],1);self.assertEqual(before,p.read_bytes());self.assertTrue((out/"manifests"/"metadata_manifest.json").exists());self.assertNotIn(str(base),json.dumps(json.loads((out/"documents"/next((out/"documents").iterdir()).name).read_text(encoding="utf-8"))))
   raw=base/"RAW_DOCUMENTS";raw.mkdir()
   with self.assertRaises(ValueError):run(raw,out)
   with self.assertRaises(ValueError):run(src,base/"PROCESSED"/"LOT_1A")
if __name__=="__main__":unittest.main()
