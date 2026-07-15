"""Synthetic-only tests for LOT 1D."""
import json, tempfile, unittest
from copy import deepcopy
from pathlib import Path
from automation.cse_memory.chunk_builder import build_document, run
from automation.cse_memory.chunk_quality import validate_coverage
from automation.cse_memory.chunk_rules import ChunkConfig, estimate_tokens

def document(blocks=None, quality="good"):
    blocks = blocks if blocks is not None else [{"block_id":"b1","block_type":"text_block","ordinal":0,"source_locator":"page 1","text":"Phrase synthétique. "*50}]
    return {"document_id":"doc-1","source_document_id":"src-1","source_relative_path":"synthetic/test.pdf","source_sha256":"a"*64,"quality_level":quality,"blocks":blocks}
def metadata():
    def v(x,c="high"): return {"value":x,"confidence_level":c}
    return {"metadata_record_id":"meta-1","document_id":"doc-1","metadata":{"year":v(2025),"instance":v("CSE"),"document_kind":v("pv"),"title":v("Document synthétique"),"metadata_quality_level":v("good")}}

class ChunkBuilderTests(unittest.TestCase):
    def test_stable_id_and_order(self):
        a,_=build_document(document(),metadata(),ChunkConfig(target_chars=200,max_chars=260,min_chars=30,overlap_chars=20),"fixed")
        b,_=build_document(document(),metadata(),ChunkConfig(target_chars=200,max_chars=260,min_chars=30,overlap_chars=20),"fixed")
        self.assertEqual([x["chunk_id"] for x in a],[x["chunk_id"] for x in b]); self.assertEqual(list(range(len(a))),[x["chunk_index"] for x in a])
    def test_large_split_max_and_complete_coverage(self):
        chunks,s=build_document(document(),metadata(),ChunkConfig(target_chars=180,max_chars=240,min_chars=20,overlap_chars=20))
        self.assertTrue(all(x["text_length_chars"]<=240 for x in chunks)); self.assertTrue(s["coverage"]["reconstruction_ok"])
    def test_small_blocks_grouped_and_blocks_preserved(self):
        bs=[{"block_id":f"b{i}","block_type":"text_block","ordinal":i,"source_locator":"page 1","text":"Texte synthétique. "} for i in range(5)]
        chunks,_=build_document(document(bs),metadata(),ChunkConfig(target_chars=200,max_chars=250,min_chars=20,overlap_chars=10))
        self.assertEqual(1,len(chunks)); self.assertEqual(5,len(chunks[0]["source_block_ids"]))
    def test_links_and_overlaps(self):
        c,_=build_document(document(),metadata(),ChunkConfig(180,240,20,30))
        self.assertEqual(0,c[0]["overlap_previous_chars"]); self.assertIsNone(c[0]["previous_chunk_id"]); self.assertIsNone(c[-1]["next_chunk_id"]); self.assertEqual(c[0]["next_chunk_id"],c[1]["chunk_id"])
    def test_locator_types(self):
        for locator,expected,field in (("page 2","page","page_numbers"),("slide 3","slide","slide_numbers"),("sheet Feuil1","sheet","sheet_names")):
            d=document([{"block_id":"b","block_type":"text_block","ordinal":0,"source_locator":locator,"text":"x"*80}]); c,_=build_document(d,metadata(),ChunkConfig(100,150,10,5)); self.assertEqual(expected,c[0]["chunk_type"]); self.assertTrue(c[0][field])
    def test_table_and_list_types(self):
        for typ,expected in (("table","table"),("list_item","list")):
            d=document([{"block_id":"b","block_type":typ,"ordinal":0,"source_locator":"page 1","text":"x"*80}]); c,_=build_document(d,metadata(),ChunkConfig(100,150,10,5)); self.assertEqual(expected,c[0]["chunk_type"])
    def test_empty_unusable_placeholder(self):
        c,s=build_document(document([],"unusable"),None,ChunkConfig()); self.assertEqual("empty_placeholder",c[0]["chunk_type"]); self.assertFalse(c[0]["indexable"]); self.assertEqual(0,s["indexable_chunk_count"])
    def test_token_estimate(self): self.assertEqual(3,estimate_tokens("abcdefghij"))
    def test_metadata_attached_and_absent_not_invented(self):
        c,_=build_document(document(),metadata(),ChunkConfig()); self.assertEqual(2025,c[0]["metadata_snapshot"]["year"]["value"])
        c,_=build_document(document(),None,ChunkConfig()); self.assertIsNone(c[0]["metadata_snapshot"]["year"]["value"])
    def test_quality_deterministic_and_short(self):
        c,_=build_document(document([{"block_id":"b","block_type":"text_block","ordinal":0,"source_locator":None,"text":"court"}]),metadata(),ChunkConfig(100,150,30,5),"fixed")
        self.assertIn("chunk_too_short",c[0]["quality_flags"]); self.assertEqual(c[0]["chunk_quality_score"],deepcopy(c)[0]["chunk_quality_score"])
    def test_strict_cut(self):
        c,_=build_document(document([{"block_id":"b","block_type":"text_block","ordinal":0,"source_locator":"page 1","text":"x"*400}]),metadata(),ChunkConfig(80,100,10,5)); self.assertTrue(any("strict_cut" in x["quality_flags"] for x in c))
    def test_artificial_loss_detected(self): self.assertFalse(validate_coverage("abcdef",["abc"])["reconstruction_ok"])
    def test_source_unchanged(self):
        d=document(); before=json.dumps(d,sort_keys=True); build_document(d,metadata(),ChunkConfig()); self.assertEqual(before,json.dumps(d,sort_keys=True))
    def test_paths_relative(self):
        c,_=build_document(document(),metadata(),ChunkConfig()); self.assertFalse(Path(c[0]["source_relative_path"]).is_absolute())
    def test_run_reports_resume_force_and_isolated_error(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ns=root/"LOT_1B"/"documents"; ms=root/"metadata"; out=root/"LOT_1D"; ns.mkdir(parents=True); ms.mkdir()
            (ns/"good.json").write_text(json.dumps(document()),encoding="utf-8"); (ns/"bad.json").write_text("{",encoding="utf-8"); (ms/"m.json").write_text(json.dumps(metadata()),encoding="utf-8")
            s=run(ns,ms,out,ChunkConfig(),"build"); self.assertEqual(1,s["errors"])
            for name in ("chunk_manifest.json","chunk_quality_report.json","chunk_coverage_report.json"): self.assertTrue((out/"manifests"/name).exists())
            s=run(ns,ms,out,ChunkConfig(),"build"); self.assertEqual(1,s["documents_skipped_resume"])
            s=run(ns,ms,out,ChunkConfig(),"build",force=True); self.assertEqual(0,s["documents_skipped_resume"])
    def test_guards(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); (r/"RAW_DOCUMENTS").mkdir(); (r/"meta").mkdir()
            with self.assertRaises(ValueError): run(r/"RAW_DOCUMENTS",r/"meta",r/"LOT_1D",ChunkConfig())
            with self.assertRaises(ValueError): run(r/"meta",r/"meta",r/"LOT_1A",ChunkConfig())
if __name__=="__main__": unittest.main()
