"""Non-destructive metadata-only audit of a local Protection sociale corpus."""
from __future__ import annotations
import argparse, hashlib, json, os, re, unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from automation.protection_sociale.document_models import stable_document_id

SUPPORTED={".pdf",".docx",".xlsx",".pptx",".txt",".csv",".rtf",".odt",".ods",".odp",".jpg",".jpeg",".png",".tif",".tiff"}
CONVERTER={".doc",".xls",".ppt",".msg",".eml"}
PERSONAL_HINTS=("nom","prenom","salari","matricule","adresse","naissance","beneficiaire","ayant droit","rib","iban","numero securite sociale")

def sha256_file(path:Path, block_size:int=1024*1024)->str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(block_size),b""): digest.update(block)
    return digest.hexdigest()

def normalized(value:str)->str:
    value=unicodedata.normalize("NFKD",value.casefold())
    return "".join(c for c in value if not unicodedata.combining(c)).replace("_"," ").replace("-"," ")

def classify_path(relative_path:str)->tuple[str,str,str|None]:
    value=normalized(relative_path)
    domain="autre"; sub=None
    if "maintien salaire" in value: domain="maintien_salaire"; sub="maintien_salaire"
    elif "prevoyance" in value: domain="prévoyance"
    elif "mutuelle" in value: domain="mutuelle"
    elif "portabilite" in value: domain="portabilité"
    elif "procedure" in value: domain="procédure_interne"
    category="autre"
    rules=(("tableau_garanties",("tableau garantie","garantie")),("cotisations",("cotisation",)),("formulaire",("formulaire",)),("courrier",("courrier",)),("procédure",("procedure",)),("notice",("notice",)),("avenant",("avenant",)),("contrat",("contrat",)),("FAQ",("faq",)),("tableau",("tableau",)))
    for candidate,terms in rules:
        if any(term in value for term in terms): category=candidate; break
    for candidate in ("incapacite","invalidite","deces","dispenses","ayants droit","beneficiaires"):
        if candidate in value: sub=candidate.replace(" ","_"); break
    return domain,category,sub

def personal_data_hint(relative_path:str)->bool:
    value=normalized(relative_path)
    return any(term in value for term in PERSONAL_HINTS)

def unusual_name(path:Path)->bool:
    return path.name!=path.name.strip() or path.name.startswith("~$") or any(unicodedata.category(c) in {"Cc","Cf","Cs","Co","Cn"} for c in path.name)

def audit_corpus(root:Path|str, *, hash_function:Callable[[Path],str]=sha256_file, long_path_threshold:int=240)->dict:
    root=Path(root).resolve()
    if not root.is_dir(): raise FileNotFoundError("Corpus directory not found")
    extensions=Counter(); domains=Counter(); categories=Counter(); hashes=defaultdict(list)
    empty=[]; unreadable=[]; long_paths=[]; unusual=[]; converters=[]; unknown=[]; personal=[]; documents=[]
    total_size=0; total_files=0; total_directories=0
    def walk_error(error:OSError): unreadable.append({"path":Path(error.filename).name if error.filename else ".","error":type(error).__name__})
    for current,dirs,files in os.walk(root,onerror=walk_error,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(current)/d).is_symlink()]; total_directories+=len(dirs)
        for filename in files:
            path=Path(current)/filename
            if path.is_symlink() or path.suffix.casefold()==".lnk": continue
            relative=path.relative_to(root).as_posix(); extension=path.suffix.casefold() or "[sans extension]"
            total_files+=1; extensions[extension]+=1
            domain,category,subcategory=classify_path(relative); domains[domain]+=1; categories[category]+=1
            if len(relative)>long_path_threshold: long_paths.append(relative)
            if unusual_name(path): unusual.append(relative)
            if extension in CONVERTER: converters.append(relative)
            if extension not in SUPPORTED and extension not in CONVERTER: unknown.append(relative)
            if personal_data_hint(relative): personal.append(relative)
            try:
                size=path.stat().st_size; digest=hash_function(path); total_size+=size
                if size==0: empty.append(relative)
                hashes[digest].append(relative)
                documents.append({"document_id":stable_document_id(relative,digest),"source_relative_path":relative,"source_extension":extension,"source_size_bytes":size,"source_sha256":digest,"document_domain":domain,"document_category":category,"document_subcategory":subcategory,"contains_personal_data_hint":relative in personal})
            except (OSError,PermissionError) as error: unreadable.append({"path":relative,"error":type(error).__name__})
    duplicates=[{"sha256":h,"files":sorted(paths),"extra_copies":len(paths)-1} for h,paths in hashes.items() if len(paths)>1]
    return {"audit_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"scope":"filenames, paths, sizes and exact-byte hashes only; no content extraction","total_files":total_files,"total_directories":total_directories,"total_size_bytes":total_size,"extensions":dict(sorted(extensions.items())),"domains":dict(sorted(domains.items())),"categories":dict(sorted(categories.items())),"empty_file_count":len(empty),"empty_files":sorted(empty),"unreadable_file_count":len(unreadable),"unreadable_files":unreadable,"duplicate_group_count":len(duplicates),"duplicate_extra_copy_count":sum(x["extra_copies"] for x in duplicates),"exact_duplicates":sorted(duplicates,key=lambda x:x["files"]),"long_path_count":len(long_paths),"long_paths":sorted(long_paths),"unusual_name_count":len(unusual),"unusual_names":sorted(unusual),"converter_required_extensions":sorted({Path(x).suffix.casefold() for x in converters}),"converter_required_files":sorted(converters),"unknown_extensions":sorted({Path(x).suffix.casefold() or "[sans extension]" for x in unknown}),"unknown_extension_files":sorted(unknown),"personal_data_hint_count":len(personal),"personal_data_hint_files":sorted(personal),"documents":sorted(documents,key=lambda x:x["source_relative_path"])}

def render_markdown(r:dict)->str:
    def counts(values): return "\n".join(f"- `{k}` : {v}" for k,v in values.items()) or "- Aucun"
    return f"""# Audit local — Protection sociale

Audit limité aux noms, chemins relatifs, tailles et empreintes binaires. Aucun contenu n'est extrait.

## Synthèse

- Fichiers : {r['total_files']}
- Dossiers : {r['total_directories']}
- Taille : {r['total_size_bytes']} octets
- Fichiers vides : {r['empty_file_count']}
- Fichiers illisibles : {r['unreadable_file_count']}
- Groupes de doublons : {r['duplicate_group_count']}
- Indices de données personnelles dans les noms ou chemins : {r['personal_data_hint_count']}

## Extensions

{counts(r['extensions'])}

## Domaines probables

{counts(r['domains'])}

## Catégories probables

{counts(r['categories'])}

## Formats nécessitant un convertisseur

{counts({x:1 for x in r['converter_required_extensions']})}

## Extensions inconnues

{counts({x:1 for x in r['unknown_extensions']})}
"""

def write_reports(report:dict,output_dir:Path|str)->tuple[Path,Path]:
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    jp=output/"protection_sociale_audit.json"; mp=output/"protection_sociale_audit.md"
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); mp.write_text(render_markdown(report),encoding="utf-8")
    return jp,mp

def main()->int:
    root=Path(__file__).resolve().parents[2]; p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus",type=Path,default=root/"PROTECTION_SOCIALE_ENGINE"/"RAW_DOCUMENTS"); p.add_argument("--output",type=Path,default=root/"PROTECTION_SOCIALE_ENGINE"/"AUDIT"); a=p.parse_args()
    report=audit_corpus(a.corpus); write_reports(report,a.output)
    print(json.dumps({k:report[k] for k in ("total_files","total_directories","total_size_bytes","extensions","domains","categories","empty_file_count","unreadable_file_count","duplicate_group_count","personal_data_hint_count")},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
