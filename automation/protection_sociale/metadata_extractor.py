"""Local deterministic metadata extraction without AI, OCR, or network."""
from __future__ import annotations
import argparse,json,re,time,uuid
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from automation.protection_sociale.metadata_models import MetadataRecord,MetadataValue,EXTRACTION_VERSION,SCHEMA_VERSION
from automation.protection_sociale.metadata_rules import THEMES,DOCUMENT_TYPES,PUBLICS,LABELS,DATE_LABELS,keyword_counts,labeled_values
from automation.protection_sociale.metadata_confidence import confidence,quality_level
ABSOLUTE=re.compile(r"(?i)[a-z]:[\\/]")
def now():return datetime.now(timezone.utc).isoformat()
def record_id(document_id:str)->str:return str(uuid.uuid5(uuid.NAMESPACE_URL,f"cfdt-nexus:protection-sociale:metadata:{document_id}:{EXTRACTION_VERSION}"))
def missing()->MetadataValue:return MetadataValue()
def value(item,source,frequency=1,contradiction=False)->MetadataValue:
    score,level=confidence(source,frequency,not contradiction,contradiction);return MetadataValue(item,source,level,score,["conflicting_candidates"] if contradiction else [])
def choose_keyword(text:str,rules:dict[str,tuple[str,...]],source="content_frequency"):
    counts={k:keyword_counts(text,v) for k,v in rules.items()};best=max(counts.values(),default=0)
    if not best:return missing(),[]
    winners=sorted(k for k,n in counts.items() if n==best);conflict=len(winners)>1
    return value(winners[0],source,best,conflict),winners if conflict else []
def extract_metadata(source:dict)->MetadataRecord:
    text=str(source.get("normalized_text") or "");path=str(source.get("source_relative_path") or "");head="\n".join(text.splitlines()[:30]);combined=path+"\n"+text
    metadata={};conflicts=[]
    domain_scores={d:sum(keyword_counts(combined,terms) for terms in themes.values()) for d,themes in THEMES.items()};best=max(domain_scores.values(),default=0)
    winners=sorted(k for k,n in domain_scores.items() if n==best and n>0)
    if winners:
        metadata["domaine_principal"]=value(winners[0],"content_frequency",best,len(winners)>1)
        if len(winners)>1:conflicts.append({"field":"domaine_principal","candidate_count":len(winners)})
        metadata["sous_domaine"],subconf=choose_keyword(combined,THEMES[winners[0]])
        if subconf:conflicts.append({"field":"sous_domaine","candidate_count":len(subconf)})
        metadata["thème_principal"]=metadata["sous_domaine"]
    else:metadata["domaine_principal"]=missing();metadata["sous_domaine"]=missing();metadata["thème_principal"]=missing()
    metadata["type_document"],typeconf=choose_keyword(path+"\n"+head,DOCUMENT_TYPES,"title")
    if typeconf:conflicts.append({"field":"type_document","candidate_count":len(typeconf)})
    for field,pattern in LABELS.items():
        values=labeled_values(head,pattern)
        metadata[field]=value(values[0],"labeled_header",1,len(values)>1) if values else missing()
        if len(values)>1:conflicts.append({"field":field,"candidate_count":len(values)})
    for field,pattern in DATE_LABELS.items():
        values=labeled_values(head,pattern);metadata[field]=value(values[0],"labeled_header",1,len(values)>1) if values else missing()
        if len(values)>1:conflicts.append({"field":field,"candidate_count":len(values)})
    public=[]
    for field,terms in PUBLICS.items():
        count=keyword_counts(combined,terms);metadata[field]=value(True,"content_frequency",count) if count else missing()
        if count:public.append(field)
    metadata["public_concerné"]=value(public,"content_frequency",len(public)) if public else missing()
    nonmissing=[v for v in metadata.values() if v.value is not None];score=round(100*sum(v.confidence_score for v in nonmissing)/max(1,len(metadata)))
    status="empty" if not text else "extracted_with_conflicts" if conflicts else "extracted"
    return MetadataRecord(record_id(str(source["document_id"])),str(source["document_id"]),str(source.get("source_document_id","")),path,str(source["source_sha256"]),status,metadata,conflicts,[],now(),score,quality_level(score))
def validate(source:Path,output:Path):
    source=source.resolve();output=output.resolve()
    if not source.is_dir():raise FileNotFoundError("LOT 1B documents source does not exist")
    op={x.casefold() for x in output.parts}
    if "raw_documents" in op or "lot_1a" in op or "lot_1b" in op:raise ValueError("Output must be LOT 1C")
    return source,output
def write_json(path:Path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def run_extraction(source:Path|str,output:Path|str,*,mode="dry-run",limit=None,force=False):
    source,output=validate(Path(source),Path(output));paths=sorted(p for p in source.glob("*.json") if not p.is_symlink());paths=paths[:limit] if limit is not None else paths
    start=time.monotonic();processed=resumed=0;errors=[];records=[];domains=Counter();subs=Counter();themes=Counter();quality=[];insurers=contracts=missing_count=conflict_count=0
    for p in paths:
        try:
            src=json.loads(p.read_text(encoding="utf-8"));rid=record_id(str(src["document_id"]));target=output/"documents"/(rid+".json")
            if mode=="extract" and target.exists() and not force:
                old=json.loads(target.read_text(encoding="utf-8"))
                if old.get("source_sha256")==src.get("source_sha256") and old.get("extraction_version")==EXTRACTION_VERSION:record=old;resumed+=1
                else:record=extract_metadata(src).to_dict();write_json(target,record);processed+=1
            elif mode=="dry-run":continue
            else:record=extract_metadata(src).to_dict();write_json(target,record);processed+=1
            records.append(record);m=record["metadata"]
            for key,counter in (("domaine_principal",domains),("sous_domaine",subs),("thème_principal",themes)):
                if m[key]["value"] is not None:counter[str(m[key]["value"])]+=1
            insurers+=m["assureur"]["value"] is not None;contracts+=m["contrat"]["value"] is not None;missing_count+=sum(v["value"] is None for v in m.values());conflict_count+=len(record["conflicts"]);quality.append(record["metadata_quality_score"])
        except Exception as exc:errors.append({"source_file":p.name,"error_code":type(exc).__name__})
    manifest={"schema_version":SCHEMA_VERSION,"extraction_version":EXTRACTION_VERSION,"mode":mode,"examined_count":len(paths),"enriched_count":len(records),"processed_count":processed,"resumed_count":resumed,"insurer_detected_count":insurers,"contract_detected_count":contracts,"domains":dict(sorted(domains.items())),"subdomains":dict(sorted(subs.items())),"themes":dict(sorted(themes.items())),"conflict_count":conflict_count,"missing_value_count":missing_count,"average_quality_score":round(sum(quality)/len(quality),2) if quality else None,"error_count":len(errors),"duration_seconds":round(time.monotonic()-start,3),"documents":[{"metadata_record_id":r["metadata_record_id"],"document_id":r["document_id"],"status":r["extraction_status"]} for r in records]}
    if mode=="extract":
        write_json(output/"manifests"/"metadata_manifest.json",manifest);write_json(output/"manifests"/"metadata_quality_report.json",{"average_quality_score":manifest["average_quality_score"]});write_json(output/"logs"/"metadata_conflicts.json",{"conflicts":[{"metadata_record_id":r["metadata_record_id"],"conflicts":r["conflicts"]} for r in records if r["conflicts"]]});write_json(output/"logs"/"metadata_errors.json",{"errors":errors});(output/"manifests"/"metadata_summary.md").write_text(f"# Métadonnées Protection sociale — LOT 1C\n\nDocuments examinés : {len(paths)}\n\nDocuments enrichis : {len(records)}\n\nAucune IA, OCR, réseau ou interprétation juridique.\n",encoding="utf-8")
    return manifest
def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--mode",choices=("dry-run","extract"),default="dry-run");p.add_argument("--limit",type=int);p.add_argument("--force",action="store_true");a=p.parse_args();print(json.dumps(run_extraction(a.source,a.output,mode=a.mode,limit=a.limit,force=a.force),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
