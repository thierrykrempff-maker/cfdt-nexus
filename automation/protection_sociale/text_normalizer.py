"""Normalize LOT 1A Protection sociale text locally and deterministically."""
from __future__ import annotations
import argparse,json,re,time,uuid
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from automation.protection_sociale.normalized_models import NormalizedDocument,NORMALIZATION_VERSION,SCHEMA_VERSION
from automation.protection_sociale.text_quality import assess_quality

SEPARATOR=re.compile(r"^---\s+(PAGE|TABLE|PARAGRAPH)\s+(.+?)\s+---$",re.I); CONTROL=re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"); ABSOLUTE=re.compile(r"(?i)(?:[a-z]:[\\/][^\r\n\t<>\"|?*]+|/(?:home|users)/[^\r\n\t<>\"|?*]+)")
def now():return datetime.now(timezone.utc).isoformat()
def normalized_id(source_id:str)->str:return str(uuid.uuid5(uuid.NAMESPACE_URL,f"cfdt-nexus:protection-sociale:normalized:{source_id}:{NORMALIZATION_VERSION}"))
def normalize_text(text:str)->tuple[str,list[str]]:
    changes=[]; value=text.replace("\r\n","\n").replace("\r","\n")
    if value!=text:changes.append("line_endings_normalized")
    updated=CONTROL.sub("",value)
    if updated!=value:changes.append("control_characters_removed")
    lines=[]; spaces=False
    for line in updated.split("\n"):
        if SEPARATOR.match(line.strip()):lines.append(line.strip());continue
        clean=re.sub(r"[ \t]+"," ",line).strip();spaces|=clean!=line;lines.append(clean)
    if spaces:changes.append("horizontal_spaces_normalized")
    compact=re.sub(r"\n{3,}","\n\n","\n".join(lines)).strip()
    if compact!="\n".join(lines).strip():changes.append("excessive_blank_lines_reduced")
    return compact,changes
def normalize_document(source:dict)->NormalizedDocument:
    original=str(source.get("text_content") or ""); normalized,changes=normalize_text(original); safe,count=ABSOLUTE.subn("[ABSOLUTE_PATH_REDACTED]",normalized)
    if count:changes.append("absolute_paths_redacted")
    quality=assess_quality(safe,source); status="empty" if not safe else ("normalized_with_warnings" if quality["flags"] else "normalized")
    return NormalizedDocument(normalized_id(str(source["document_id"])),str(source["document_id"]),str(source["source_relative_path"]),str(source["source_sha256"]),str(source.get("extraction_status","unknown")),status,NORMALIZATION_VERSION,len(original),len(safe),safe,source.get("page_count"),source.get("paragraph_count"),source.get("table_count"),quality["score"],quality["level"],quality["flags"],changes,quality["warnings"],now())
def validate(source:Path,output:Path)->tuple[Path,Path]:
    source=source.resolve();output=output.resolve()
    if not source.is_dir():raise FileNotFoundError("LOT 1A documents source does not exist")
    op={x.casefold() for x in output.parts};sp={x.casefold() for x in source.parts}
    if "raw_documents" in sp:raise ValueError("Source must be LOT 1A, not RAW_DOCUMENTS")
    if "raw_documents" in op or "lot_1a" in op:raise ValueError("Output must be LOT 1B, not RAW_DOCUMENTS or LOT 1A")
    if source.is_symlink() or output.is_symlink():raise ValueError("Symbolic links are refused")
    return source,output
def write_json(path:Path,value)->None:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def run_normalization(source:Path|str,output:Path|str,*,mode="dry-run",limit=None,force=False)->dict:
    source,output=validate(Path(source),Path(output));paths=[p for p in sorted(source.glob("*.json")) if not p.is_symlink()];paths=paths[:limit] if limit is not None else paths
    started=time.monotonic();statuses=Counter();levels=Counter();scores=[];docs=[];errors=[];original=normalized=processed=resumed=empty=0
    for p in paths:
        try:
            item=json.loads(p.read_text(encoding="utf-8"));oid=normalized_id(str(item["document_id"]));target=output/"documents"/(oid+".json")
            if mode=="normalize" and target.exists() and not force:
                previous=json.loads(target.read_text(encoding="utf-8"))
                if previous.get("source_sha256")==item.get("source_sha256") and previous.get("normalization_version")==NORMALIZATION_VERSION:
                    resumed+=1;statuses[previous["normalization_status"]]+=1;levels[previous["quality_level"]]+=1;scores.append(previous["quality_score"]);original+=previous["original_text_length"];normalized+=previous["normalized_text_length"];empty+=previous["normalization_status"]=="empty";continue
            if mode=="dry-run":statuses["normalizable"]+=1;empty+=not bool(item.get("text_content"));continue
            record=normalize_document(item);write_json(target,record.to_dict());processed+=1;statuses[record.normalization_status]+=1;levels[record.quality_level]+=1;scores.append(record.quality_score);original+=record.original_text_length;normalized+=record.normalized_text_length;empty+=record.normalization_status=="empty";docs.append({"document_id":record.document_id,"source_document_id":record.source_document_id,"status":record.normalization_status,"quality_level":record.quality_level})
        except Exception as exc:errors.append({"source_file":p.name,"error_code":type(exc).__name__});statuses["failed"]+=1
    manifest={"schema_version":SCHEMA_VERSION,"normalization_version":NORMALIZATION_VERSION,"mode":mode,"examined_count":len(paths),"normalized_count":processed,"resumed_count":resumed,"empty_count":empty,"original_text_length_total":original,"normalized_text_length_total":normalized,"average_quality_score":round(sum(scores)/len(scores),2) if scores else None,"quality_levels":dict(sorted(levels.items())),"status_counts":dict(sorted(statuses.items())),"error_count":len(errors),"duration_seconds":round(time.monotonic()-started,3),"documents":docs}
    if mode=="normalize":
        write_json(output/"manifests"/"normalization_manifest.json",manifest);write_json(output/"manifests"/"quality_report.json",{"average_quality_score":manifest["average_quality_score"],"quality_levels":manifest["quality_levels"]});write_json(output/"logs"/"normalization_errors.json",{"errors":errors})
        (output/"manifests"/"normalization_summary.md").write_text(f"# Normalisation Protection sociale — LOT 1B\n\nDocuments examinés : {len(paths)}\n\nDocuments normalisés : {processed}\n\nAucune IA, OCR, réseau ou analyse métier.\n",encoding="utf-8")
    return manifest
def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--mode",choices=("dry-run","normalize"),default="dry-run");p.add_argument("--limit",type=int);p.add_argument("--force",action="store_true");a=p.parse_args();m=run_normalization(a.source,a.output,mode=a.mode,limit=a.limit,force=a.force);print(json.dumps({k:m[k] for k in ("mode","examined_count","normalized_count","resumed_count","empty_count","original_text_length_total","normalized_text_length_total","average_quality_score","quality_levels","status_counts","error_count","duration_seconds")},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
