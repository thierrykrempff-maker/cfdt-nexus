"""Build local deterministic chunks from LOT 1B and LOT 1C JSON files."""
from __future__ import annotations
import argparse, hashlib, json, re, time, uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from automation.cse_memory.chunk_models import Chunk, CHUNKING_VERSION
from automation.cse_memory.chunk_quality import assess_chunk, validate_coverage
from automation.cse_memory.chunk_rules import ChunkConfig, estimate_tokens, overlap_prefix, split_text

def utc_now(): return datetime.now(timezone.utc).isoformat()
def stable_chunk_id(document_id: str, index: int, unique_text: str) -> str:
    digest=hashlib.sha256(unique_text.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL,f"cfdt-nexus:cse:chunk:{document_id}:{index}:{digest}:{CHUNKING_VERSION}"))

def _guard(source: Path, output: Path) -> None:
    s=source.resolve(); o=output.resolve(); su=str(s).replace("\\","/").upper(); ou=str(o).replace("\\","/").upper()
    if "RAW_DOCUMENTS" in su: raise ValueError("RAW_DOCUMENTS cannot be used as a source")
    if any(x in ou for x in ("RAW_DOCUMENTS","/LOT_1A","/LOT_1B","/LOT_1C")): raise ValueError("unsafe output location")
    if source.is_symlink() or output.is_symlink(): raise ValueError("symbolic links are refused")

def _metadata_snapshot(record: dict[str,Any]|None) -> dict[str,Any]:
    metadata=(record or {}).get("metadata",{}); out={}
    for key in ("meeting_date","year","instance","meeting_type","document_kind","document_status","title","pv_number","meeting_number"):
        item=metadata.get(key,{})
        out[key]={"value":item.get("value"),"confidence_level":item.get("confidence_level","very_low")}
    return out

def _locator_data(locators:list[str]) -> tuple[list[int],list[int],list[str]]:
    pages=[]; slides=[]; sheets=[]
    for value in locators:
        m=re.match(r"page\s+(\d+)",value,re.I)
        if m: pages.append(int(m.group(1)))
        m=re.match(r"slide\s+(\d+)",value,re.I)
        if m: slides.append(int(m.group(1)))
        m=re.match(r"sheet\s+(.+)",value,re.I)
        if m: sheets.append(m.group(1))
    return sorted(set(pages)),sorted(set(slides)),list(dict.fromkeys(sheets))

def _chunk_type(block_types:list[str], locators:list[str]) -> str:
    types=set(block_types)
    if any("table" in x for x in types): return "table"
    if types and types <= {"list_item","list"}: return "list"
    kinds={x.split()[0].lower() for x in locators if x}
    if kinds=={"page"}: return "page"
    if kinds=={"slide"}: return "slide"
    if kinds=={"sheet"}: return "sheet"
    return "mixed" if len(types)>1 or len(kinds)>1 else "text"

def build_document(doc:dict[str,Any], metadata:dict[str,Any]|None, config:ChunkConfig, created_at:str|None=None) -> tuple[list[dict],dict]:
    config.validate(); created_at=created_at or utc_now(); blocks=[b for b in doc.get("blocks",[]) if b.get("block_type")!="separator" and b.get("text")]
    snapshot=_metadata_snapshot(metadata); document_id=doc["document_id"]
    if not blocks:
        cid=stable_chunk_id(document_id,0,""); score,level,flags=assess_chunk("",0,config.min_chars,config.max_chars,0,doc.get("quality_level","unusable"),[],snapshot)
        chunk=Chunk(cid,document_id,doc.get("source_document_id",""),(metadata or {}).get("metadata_record_id"),doc.get("source_relative_path",""),doc.get("source_sha256",""),0,1,"empty_placeholder","",0,0,[],None,None,[],[],[],[],None,None,0,0,snapshot,doc.get("quality_level","unusable"),(metadata or {}).get("metadata",{}).get("metadata_quality_level",{}).get("value","unusable"),score,level,flags,["no_exploitable_text"],created_at=created_at,indexable=False,unique_text_length_chars=0)
        cov=validate_coverage("",[]); return [chunk.to_dict()],{"document_id":document_id,"chunk_count":1,"indexable_chunk_count":0,"coverage":cov,"excluded_blocks":len(doc.get("blocks",[]))}
    atoms=[]
    for bi,b in enumerate(blocks):
        suffix="\n\n" if bi<len(blocks)-1 else ""
        for piece,strict in split_text(b["text"]+suffix,config.max_chars,config.target_chars):
            atoms.append({"text":piece,"ids":[b["block_id"]],"types":[b.get("block_type","text")],"locators":[b.get("source_locator")] if b.get("source_locator") else [],"strict":strict})
    cores=[]; current=None
    for atom in atoms:
        locator_change=current and current["locators"] and atom["locators"] and current["locators"][-1]!=atom["locators"][0]
        if current and (len(current["text"])+len(atom["text"])>config.target_chars or locator_change and len(current["text"])>=config.min_chars):
            cores.append(current); current=None
        if current is None: current={k:(list(v) if isinstance(v,list) else v) for k,v in atom.items()}
        else:
            current["text"]+=atom["text"]; current["ids"]+=atom["ids"]; current["types"]+=atom["types"]; current["locators"]+=atom["locators"]; current["strict"]|=atom["strict"]
    if current: cores.append(current)
    source_text="".join(a["text"] for a in atoms); ids=[stable_chunk_id(document_id,i,c["text"]) for i,c in enumerate(cores)]; chunks=[]
    for i,core in enumerate(cores):
        prefix="" if i==0 else overlap_prefix(cores[i-1]["text"],config.overlap_chars,config.max_chars-len(core["text"]))
        text=prefix+core["text"]; loc=list(dict.fromkeys(core["locators"])); pages,slides,sheets=_locator_data(loc)
        score,level,flags=assess_chunk(text,len(core["text"]),config.min_chars,config.max_chars,len(prefix),doc.get("quality_level","unusable"),loc,snapshot,core["strict"])
        chunk=Chunk(ids[i],document_id,doc.get("source_document_id",""),(metadata or {}).get("metadata_record_id"),doc.get("source_relative_path",""),doc.get("source_sha256",""),i,len(cores),_chunk_type(core["types"],loc),text,len(text),estimate_tokens(text),list(dict.fromkeys(core["ids"])),core["ids"][0],core["ids"][-1],loc,pages,slides,sheets,ids[i-1] if i else None,ids[i+1] if i+1<len(ids) else None,len(prefix),0,snapshot,doc.get("quality_level","unusable"),(metadata or {}).get("metadata",{}).get("metadata_quality_level",{}).get("value","unusable"),score,level,flags,["strict_cut_required"] if core["strict"] else [],created_at=created_at,unique_text_length_chars=len(core["text"]))
        chunks.append(chunk.to_dict())
    for i in range(len(chunks)-1): chunks[i]["overlap_next_chars"]=chunks[i+1]["overlap_previous_chars"]
    cov=validate_coverage(source_text,[c["text"] for c in cores]); cov["overlap_characters"]=sum(c["overlap_previous_chars"] for c in chunks)
    return chunks,{"document_id":document_id,"chunk_count":len(chunks),"indexable_chunk_count":len(chunks),"coverage":cov,"excluded_blocks":len(doc.get("blocks",[]))-len(blocks)}

def run(normalized_source:Path,metadata_source:Path,output:Path,config:ChunkConfig,mode="dry-run",limit=None,force=False,filters=None) -> dict:
    _guard(normalized_source,output); _guard(metadata_source,output); started=time.perf_counter(); filters=filters or {}
    metadata_by_doc={}
    for p in sorted(metadata_source.glob("*.json")):
        if p.is_symlink(): continue
        r=json.loads(p.read_text(encoding="utf-8")); metadata_by_doc[r.get("document_id")]=r
    results=[]; errors=[]; processed=0; skipped=0
    files=[p for p in sorted(normalized_source.glob("*.json")) if not p.is_symlink() and p.suffix.lower()!=".lnk"]
    for p in files:
        try:
            doc=json.loads(p.read_text(encoding="utf-8")); meta=metadata_by_doc.get(doc.get("document_id")); snap=_metadata_snapshot(meta)
            if filters.get("extension") and Path(doc.get("source_relative_path","")).suffix.lower()!=filters["extension"].lower(): continue
            if filters.get("subfolder") and filters["subfolder"].lower() not in doc.get("source_relative_path","").lower(): continue
            if filters.get("quality") and doc.get("quality_level")!=filters["quality"]: continue
            if filters.get("instance") and snap["instance"]["value"]!=filters["instance"]: continue
            if filters.get("document_kind") and snap["document_kind"]["value"]!=filters["document_kind"]: continue
            if filters.get("metadata_quality") and (meta or {}).get("metadata",{}).get("metadata_quality_level",{}).get("value")!=filters["metadata_quality"]: continue
            if limit is not None and processed>=limit: break
            chunks,summary=build_document(doc,meta,config); processed+=1; results.append((doc,chunks,summary))
            if mode=="build":
                dp=output/"documents"/(doc["document_id"]+".json"); cp=output/"chunks"/(doc["document_id"]+".jsonl")
                if dp.exists() and cp.exists() and not force: skipped+=1; continue
                dp.parent.mkdir(parents=True,exist_ok=True); cp.parent.mkdir(parents=True,exist_ok=True)
                dp.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                cp.write_text("".join(json.dumps(c,ensure_ascii=False)+"\n" for c in chunks),encoding="utf-8")
        except Exception as exc: errors.append({"file":p.name,"error":type(exc).__name__,"message":str(exc)})
    chunks=[c for _,cs,_ in results for c in cs]; cover=[s["coverage"] for _,_,s in results]; qualities=Counter(c["chunk_quality_level"] for c in chunks)
    stats={"mode":mode,"documents_examined":len(files),"documents_processed":processed,"documents_skipped_resume":skipped,"non_indexable_documents":sum(not any(c["indexable"] for c in cs) for _,cs,_ in results),"total_chunks":len(chunks),"indexable_chunks":sum(c["indexable"] for c in chunks),"chunk_quality_levels":dict(sorted(qualities.items())),"strict_cuts":sum("strict_cut" in c["quality_flags"] for c in chunks),"too_short":sum("chunk_too_short" in c["quality_flags"] for c in chunks),"too_long":sum("chunk_too_long" in c["quality_flags"] for c in chunks),"total_estimated_tokens":sum(c["estimated_token_count"] for c in chunks),"overlap_characters":sum(c["overlap_previous_chars"] for c in chunks),"coverage_rate":round(sum(x["coverage_rate"] for x in cover)/len(cover),3) if cover else 100.0,"errors":len(errors),"duration_seconds":round(time.perf_counter()-started,3)}
    counts=[len(cs) for _,cs,_ in results]; sizes=[c["text_length_chars"] for c in chunks]
    stats.update({"chunks_per_document":{"min":min(counts,default=0),"max":max(counts,default=0),"average":round(sum(counts)/len(counts),2) if counts else 0},"chunk_sizes":{"min":min(sizes,default=0),"max":max(sizes,default=0),"average":round(sum(sizes)/len(sizes),2) if sizes else 0}})
    if mode=="build":
        m=output/"manifests"; l=output/"logs"; m.mkdir(parents=True,exist_ok=True); l.mkdir(parents=True,exist_ok=True)
        manifest={"chunking_version":CHUNKING_VERSION,"configuration":config.__dict__,"statistics":stats,"documents":[s for _,_,s in results]}
        (m/"chunk_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (m/"chunk_quality_report.json").write_text(json.dumps({"statistics":stats,"quality_levels":stats["chunk_quality_levels"]},indent=2)+"\n",encoding="utf-8")
        (m/"chunk_coverage_report.json").write_text(json.dumps({"coverage_rate":stats["coverage_rate"],"documents":[s["coverage"]|{"document_id":s["document_id"]} for _,_,s in results]},indent=2)+"\n",encoding="utf-8")
        (m/"chunk_summary.md").write_text(f"# LOT 1D - synthèse technique\n\nDocuments traités : {processed}\n\nChunks : {len(chunks)}\n\nCouverture : {stats['coverage_rate']} %\n",encoding="utf-8")
        (l/"chunk_errors.json").write_text(json.dumps(errors,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return stats

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--normalized-source",type=Path,required=True); p.add_argument("--metadata-source",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--mode",choices=("dry-run","build"),default="dry-run"); p.add_argument("--limit",type=int); p.add_argument("--force",action="store_true"); p.add_argument("--target-chars",type=int,default=1600); p.add_argument("--max-chars",type=int,default=2500); p.add_argument("--min-chars",type=int,default=300); p.add_argument("--overlap-chars",type=int,default=200); p.add_argument("--extension"); p.add_argument("--instance"); p.add_argument("--document-kind"); p.add_argument("--quality"); p.add_argument("--metadata-quality"); p.add_argument("--subfolder"); p.add_argument("--statistics-only",action="store_true")
    a=p.parse_args(argv); cfg=ChunkConfig(a.target_chars,a.max_chars,a.min_chars,a.overlap_chars); filters={k:getattr(a,k) for k in ("extension","instance","document_kind","quality","metadata_quality","subfolder") if getattr(a,k)}
    print(json.dumps(run(a.normalized_source,a.metadata_source,a.output,cfg,a.mode,a.limit,a.force,filters),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
