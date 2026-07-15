"""Local deterministic metadata extraction for normalized LOT 1B records."""
from __future__ import annotations
import argparse,json,time,uuid
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from automation.cse_memory.document_importer import redact_absolute_paths
from automation.cse_memory.audit_cse_corpus import detect_family
from automation.cse_memory.metadata_models import EXTRACTION_VERSION,SCHEMA_VERSION,MetadataRecord,MetadataValue
from automation.cse_memory.metadata_confidence import arbitrate,metadata_quality,confidence_level
from automation.cse_memory.metadata_rules import date_candidates,year_hints,categorical_candidates,INSTANCE_PATTERNS,MEETING_PATTERNS,KIND_PATTERNS,STATUS_PATTERNS,probable_title,number_candidates

def now(): return datetime.now(timezone.utc).isoformat()
def record_id(document_id): return str(uuid.uuid5(uuid.NAMESPACE_URL,f"cfdt-nexus:cse:metadata:{document_id}:{EXTRACTION_VERSION}"))
def derived(value, rule): return MetadataValue(value=value,confidence=1.0,confidence_level="very_high",detected_from=["meeting_date"],evidence_type="derived",rule_id=rule) if value is not None else MetadataValue(rule_id=rule,warnings=["metadata_missing"])

def extract_metadata(source:dict[str,Any])->MetadataRecord:
    document_id=str(source["document_id"]); path=str(source.get("source_relative_path",'')); filename=Path(path).name; folder=str(Path(path).parent)
    blocks=source.get("blocks",[]); first="\n".join(str(b.get("text",'')) for b in blocks[:5]); body=str(source.get("normalized_text",'')); title=probable_title(blocks)
    texts=[("first_block",first),("filename",filename),("folder",folder),("body",body)]
    dates=date_candidates(first,"first_block")+date_candidates(filename,"filename")+date_candidates(body,"body")
    values={
      "meeting_date":arbitrate(dates,"DATE_MISSING"),
      "instance":arbitrate(categorical_candidates(texts,INSTANCE_PATTERNS,"INSTANCE"),"INSTANCE_MISSING"),
      "meeting_type":arbitrate(categorical_candidates(texts,MEETING_PATTERNS,"MEETING_TYPE"),"MEETING_TYPE_MISSING"),
      "document_kind":arbitrate(categorical_candidates(texts,KIND_PATTERNS,"DOCUMENT_KIND"),"DOCUMENT_KIND_MISSING"),
      "document_status":arbitrate(categorical_candidates(texts,STATUS_PATTERNS,"DOCUMENT_STATUS"),"DOCUMENT_STATUS_MISSING"),
      "meeting_number":arbitrate(number_candidates(texts),"MEETING_NUMBER_MISSING"),
      "title":MetadataValue(value=title,confidence=.85 if title else 0,confidence_level="high" if title else "very_low",detected_from=["internal_title"] if title else [],evidence_type="block_locator" if title else None,rule_id="TITLE_FIRST_STRUCTURED_BLOCK" if title else "TITLE_MISSING",warnings=[] if title else ["metadata_missing"]),
      "source_period_hint":arbitrate(year_hints(folder),"SOURCE_PERIOD_MISSING"),
      "language_hint":MetadataValue(value=source.get("detected_language_hint"),confidence=.7 if source.get("detected_language_hint") else 0,confidence_level="medium" if source.get("detected_language_hint") else "very_low",detected_from=["lot_1b"] if source.get("detected_language_hint") else [],evidence_type="local_hint",rule_id="LANGUAGE_LOT1B_HINT"),
    }
    conflicts=[]
    for key in ("meeting_date","instance","document_kind","document_status"):
        if values[key].alternatives: conflicts.append({"type":f"conflicting_{key}","rule_id":f"CONFLICT_{key.upper()}","candidate_count":1+len(values[key].alternatives)})
    path_years={int(y) for y in __import__('re').findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)",path)}
    if path_years & {1964,2054}: conflicts.append({"type":"suspicious_path_year","rule_id":"CONFLICT_SUSPICIOUS_YEAR_1964_2054","candidate_count":len(path_years & {1964,2054})})
    date_value=values["meeting_date"].value
    if date_value:
        y,m,_=map(int,date_value.split('-')); values["year"]=derived(y,"YEAR_FROM_MEETING_DATE"); values["month"]=derived(m,"MONTH_FROM_MEETING_DATE"); values["quarter"]=derived((m-1)//3+1,"QUARTER_FROM_MEETING_DATE")
        if path_years and y not in path_years: conflicts.append({"type":"filename_text_year_mismatch","rule_id":"CONFLICT_FILENAME_TEXT_YEAR","candidate_count":1+len(path_years)})
    else:
        values["year"]=MetadataValue(rule_id="YEAR_MISSING",warnings=["metadata_missing"]); values["month"]=MetadataValue(rule_id="MONTH_MISSING",warnings=["metadata_missing"]); values["quarter"]=MetadataValue(rule_id="QUARTER_MISSING",warnings=["metadata_missing"])
    first_instance=arbitrate(categorical_candidates([("first_block",first)],INSTANCE_PATTERNS,"INSTANCE"),"M").value; folder_instance=arbitrate(categorical_candidates([("folder",folder)],INSTANCE_PATTERNS,"INSTANCE"),"M").value
    if first_instance and folder_instance and first_instance!=folder_instance: conflicts.append({"type":"path_text_instance_mismatch","rule_id":"CONFLICT_PATH_TEXT_INSTANCE","candidate_count":2})
    first_kind=arbitrate(categorical_candidates([("first_block",first)],KIND_PATTERNS,"KIND"),"M").value; file_kind=arbitrate(categorical_candidates([("filename",filename)],KIND_PATTERNS,"KIND"),"M").value
    if first_kind and file_kind and first_kind!=file_kind: conflicts.append({"type":"filename_text_document_kind_mismatch","rule_id":"CONFLICT_FILENAME_TEXT_KIND","candidate_count":2})
    status_values={c["value"] for c in categorical_candidates(texts,STATUS_PATTERNS,"STATUS")}
    if "draft" in status_values and ({"final","approved"}&status_values): conflicts.append({"type":"draft_and_final_status","rule_id":"CONFLICT_DRAFT_FINAL","candidate_count":2})
    score,level=metadata_quality(values,conflicts)
    values["metadata_quality_score"]=derived(score,"METADATA_QUALITY_DETERMINISTIC"); values["metadata_quality_level"]=derived(level,"METADATA_QUALITY_LEVEL")
    missing=sum(v.value is None for k,v in values.items() if k not in {"metadata_quality_score","metadata_quality_level"})
    warnings=["insufficient_metadata"] if missing>=6 else []
    safe_path,_=redact_absolute_paths(path)
    return MetadataRecord(record_id(document_id),document_id,str(source.get("source_document_id",document_id)),safe_path,str(source.get("source_sha256",'')),SCHEMA_VERSION,EXTRACTION_VERSION,"extracted_with_warnings" if warnings or conflicts else "extracted",now(),warnings,conflicts,{"rules_triggered":sum(v.value is not None for v in values.values()),"missing_values":missing},values)

def validate(source:Path,output:Path):
    source=source.resolve();output=output.resolve()
    if not source.is_dir(): raise FileNotFoundError(source)
    if "raw_documents" in {p.casefold() for p in source.parts}: raise ValueError("RAW_DOCUMENTS source forbidden")
    if {"raw_documents","lot_1a","lot_1b"}&{p.casefold() for p in output.parts}: raise ValueError("output in RAW_DOCUMENTS/LOT_1A/LOT_1B forbidden")
    return source,output
def write_json(path,value): path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def run(source,output,mode="dry-run",limit=None,force=False,extensions=None,families=None,qualities=None,subfolder=None):
    source,output=validate(Path(source),Path(output)); paths=sorted(p for p in source.glob('*.json') if not p.is_symlink())
    selected=[]
    for p in paths:
      try:d=json.loads(p.read_text(encoding='utf-8'))
      except Exception:selected.append(p);continue
      rel=str(d.get('source_relative_path',''))
      if extensions and Path(rel).suffix.casefold() not in extensions:continue
      if families and detect_family(rel).casefold() not in families:continue
      if qualities and str(d.get('quality_level','')).casefold() not in qualities:continue
      if subfolder and not rel.casefold().startswith(subfolder.casefold().strip('/\\')):continue
      selected.append(p)
    paths=selected[:limit] if limit is not None else selected; started=time.monotonic(); counts=Counter();levels=Counter();instances=Counter();kinds=Counter();conflicts=[];errors=[];docs=[];resumed=0
    for p in paths:
      try:
        source_doc=json.loads(p.read_text(encoding='utf-8')); rid=record_id(source_doc['document_id']); out=output/'documents'/f'{rid}.json'
        if mode=='extract' and out.exists() and not force:
          old=json.loads(out.read_text(encoding='utf-8'))
          if old.get('source_sha256')==source_doc.get('source_sha256') and old.get('extraction_version')==EXTRACTION_VERSION: resumed+=1;counts[old['extraction_status']]+=1;continue
        if mode=='dry-run':counts['extractable']+=1;continue
        rec=extract_metadata(source_doc);data=rec.to_dict();write_json(out,data);counts[rec.extraction_status]+=1
        md=data['metadata'];levels[md['meeting_date']['confidence_level']]+=1;instances[str(md['instance']['value'])]+=1;kinds[str(md['document_kind']['value'])]+=1;conflicts.extend({"metadata_record_id":rid,**c} for c in rec.conflicts);docs.append({"metadata_record_id":rid,"status":rec.extraction_status,"quality_score":md['metadata_quality_score']['value']})
      except Exception as e:
        safe,_=redact_absolute_paths(str(e)[:300]);errors.append({"source_record":p.stem,"error_code":type(e).__name__,"error_message":safe});counts['failed']+=1
    manifest={"mode":mode,"examined_count":len(paths),"enriched_count":len(docs),"resumed_count":resumed,"status_counts":dict(counts),"date_confidence_levels":dict(levels),"instances":dict(instances),"document_kinds":dict(kinds),"conflict_count":len(conflicts),"error_count":len(errors),"duration_seconds":round(time.monotonic()-started,3),"documents":docs}
    if mode=='extract':
      write_json(output/'manifests'/'metadata_manifest.json',manifest);write_json(output/'manifests'/'metadata_quality_report.json',{"quality_scores":dict(Counter(str(d['quality_score']) for d in docs))});write_json(output/'logs'/'metadata_errors.json',{"errors":errors});write_json(output/'logs'/'metadata_conflicts.json',{"conflicts":conflicts});(output/'manifests'/'metadata_summary.md').write_text(f"# LOT 1C\n\nDocuments: {len(docs)}\nConflits: {len(conflicts)}\nErreurs: {len(errors)}\n",encoding='utf-8')
    return manifest

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=['dry-run','extract'],default='dry-run');p.add_argument('--limit',type=int);p.add_argument('--force',action='store_true');p.add_argument('--extension',action='append');p.add_argument('--family',action='append');p.add_argument('--quality',action='append');p.add_argument('--subfolder');p.add_argument('--statistics-only',action='store_true');a=p.parse_args();ext={x.casefold() if x.startswith('.') else '.'+x.casefold() for x in a.extension or []};result=run(a.source,a.output,a.mode,a.limit,a.force,ext or None,{x.casefold() for x in a.family or []} or None,{x.casefold() for x in a.quality or []} or None,a.subfolder);result.pop('documents',None) if a.statistics_only else None;print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
