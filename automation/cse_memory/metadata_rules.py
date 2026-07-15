"""Stable, explicit documentary metadata rules."""
from __future__ import annotations
import re
import unicodedata
from datetime import date
from pathlib import PurePosixPath
from typing import Any
from automation.cse_memory.metadata_confidence import SOURCE_WEIGHTS

MONTHS = {"janvier":1,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"aout":8,"septembre":9,"octobre":10,"novembre":11,"decembre":12}
RULES = {
 "DATE_FIRST_PAGE_EXPLICIT":{"weight":.90,"sources":["first_block"],"description":"Explicit valid date in first block"},
 "DATE_FILENAME_NUMERIC":{"weight":.72,"sources":["filename"],"description":"Valid date in filename"},
 "DATE_FOLDER_YEAR_ONLY":{"weight":.35,"sources":["folder"],"description":"Year-only folder hint"},
 "INSTANCE_FIRST_BLOCK":{"weight":.90,"sources":["first_block"],"description":"Instance keyword in first block"},
 "DOCUMENT_KIND_FILENAME":{"weight":.72,"sources":["filename"],"description":"Document kind in filename"},
}

def plain(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))

def _valid(year:int, month:int, day:int) -> str | None:
    try:
        if year < 1990 or year > 2035: return None
        return date(year,month,day).isoformat()
    except ValueError: return None

def date_candidates(text: str, source: str, first_only: bool=False) -> list[dict[str,Any]]:
    value = plain(text)
    found=[]
    patterns=[
      (r"\b(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b", lambda m:(int(m[1]),int(m[2]),int(m[3]))),
      (r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2})\b", lambda m:(int(m[3]),int(m[2]),int(m[1]))),
      (r"\b(0?[1-9]|[12]\d|3[01])\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+(20\d{2})\b", lambda m:(int(m[3]),MONTHS[m[2]],int(m[1]))),
    ]
    for pattern, convert in patterns:
        for match in re.finditer(pattern,value):
            iso=_valid(*convert(match))
            if iso:
                rule="DATE_FIRST_PAGE_EXPLICIT" if source=="first_block" else "DATE_FILENAME_NUMERIC" if source=="filename" else "DATE_BODY_EXPLICIT"
                found.append({"value":iso,"source":source,"weight":SOURCE_WEIGHTS[source],"rule_id":rule,"agreement_rule":"DATE_FIRST_PAGE_AND_FILENAME_AGREE","evidence_type":"date_pattern"})
    return found

def year_hints(path: str) -> list[dict[str,Any]]:
    years={int(y) for y in re.findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)",path)}
    return [{"value":str(y),"source":"folder","weight":.35 if 1990<=y<=2035 else .1,"rule_id":"DATE_FOLDER_YEAR_ONLY","evidence_type":"path_year"} for y in years]

INSTANCE_PATTERNS=[("CSSCT",r"\bcssct\b"),("CHSCT",r"\bchsct\b"),("CCE",r"\bcce\b|comite central"),("CSE",r"\bcse\b"),("CE",r"\bce\b|comite d'etablissement"),("NAO",r"\bnao\b"),("commission",r"\bcommission\b")]
MEETING_PATTERNS=[("extraordinaire",r"extraordinaire"),("exceptionnelle",r"exceptionnelle"),("preparatoire",r"preparatoire"),("pleniere",r"pleniere"),("commission",r"commission"),("consultation",r"consultation"),("negociation",r"negociation"),("ordinaire",r"\bordinaire\b")]
KIND_PATTERNS=[("projet de proces-verbal",r"projet\s+(?:de\s+)?p\.?v\.?|projet\s+de\s+proces.?verbal"),("ordre du jour",r"ordre du jour|\bodj\b"),("proces-verbal",r"\bp\.?v\.?(?:\s|$)|proces.?verbal"),("compte rendu",r"compte rendu"),("convocation",r"convocation"),("presentation",r"presentation"),("annexe",r"annexe"),("consultation",r"consultation"),("expertise",r"expertise"),("accord",r"\baccord\b"),("note",r"\bnote\b"),("courrier",r"courrier"),("tableau",r"tableau"),("archive",r"archive|\.zip")]
STATUS_PATTERNS=[("draft",r"projet|brouillon|provisoire"),("approved",r"approuve|adopte"),("signed",r"\bsigne\b|signature"),("unsigned",r"non signe"),("amended",r"amende|avenant"),("final",r"definiti(?:f|ve)|\bfinal\b")]

def categorical_candidates(texts: list[tuple[str,str]], patterns:list[tuple[str,str]], rule_prefix:str) -> list[dict[str,Any]]:
    result=[]
    for source,text in texts:
        normalized=plain(text).replace("_", " ")
        for value,pattern in patterns:
            if re.search(pattern,normalized): result.append({"value":value,"source":source,"weight":SOURCE_WEIGHTS[source],"rule_id":f"{rule_prefix}_{source.upper()}_{value.upper().replace(' ','_')}","evidence_type":"keyword"})
    return result

def probable_title(blocks:list[dict[str,Any]]) -> str | None:
    for block in blocks[:5]:
        text=str(block.get("text","")).strip()
        if block.get("block_type")!="separator" and 5<=len(text)<=180 and "\n" not in text: return text
    return None

def number_candidates(texts:list[tuple[str,str]]) -> list[dict[str,Any]]:
    result=[]
    for source,text in texts:
        for match in re.finditer(r"(?i)\b(?:p\.?v\.?|reunion)\s*(?:n[°o]|numero)?\s*([1-9]\d{0,2})\b",plain(text)):
            result.append({"value":match.group(1),"source":source,"weight":SOURCE_WEIGHTS[source],"rule_id":"PV_OR_MEETING_NUMBER_EXPLICIT","evidence_type":"number_pattern"})
    return result
