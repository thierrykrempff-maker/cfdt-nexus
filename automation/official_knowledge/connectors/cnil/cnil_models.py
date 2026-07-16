"""Synthetic-safe CNIL resource and connector contracts."""
from __future__ import annotations
from dataclasses import asdict,dataclass,field
from datetime import date
from typing import Any
import uuid
from automation.official_knowledge.fingerprints import canonicalize_uri

RESOURCE_TYPES={"web_guidance","news","press_release","guide","report","deliberation","sanction","faq","definition","downloadable_document","open_dataset","video_metadata","unknown"}

def stable_resource_id(uri:str)->str:return str(uuid.uuid5(uuid.NAMESPACE_URL,"cfdt-nexus:cnil:"+canonicalize_uri(uri)))

@dataclass(frozen=True)
class ResourceCandidate:
 canonical_uri:str; resource_type:str="unknown"; title:str=""; theme_tags:tuple[str,...]=(); audience_tags:tuple[str,...]=(); retrieval_mode:str="targeted_page"; content_format:str="text/html"
 def __post_init__(self):
  if self.resource_type not in RESOURCE_TYPES:raise ValueError("invalid resource_type")

@dataclass(frozen=True)
class CnilResource:
 cnil_resource_id:str; source_id:str; canonical_uri:str; resource_type:str; title:str
 publication_date:date|None=None; modification_date:date|None=None; theme_tags:tuple[str,...]=(); audience_tags:tuple[str,...]=()
 authority_level:str="official_guidance"; license_id:str|None=None; license_review_status:str="pending"; retrieval_mode:str="targeted_page"
 language:str="fr"; content_format:str="text/html"; document_uri:str|None=None; content_sha256:str|None=None
 indexable:bool=False; rejection_reason:str|None=None; provenance:dict[str,Any]=field(default_factory=dict); warnings:tuple[str,...]=(); schema_version:str="1.0"
 def __post_init__(self):
  if self.source_id!="cnil":raise ValueError("invalid source")
  for value in (self.canonical_uri,self.document_uri):
   if value and (len(value)>1 and value[1]==":" or value.startswith(("/home/","/Users/"))):raise ValueError("absolute path refused")
 def to_dict(self):return asdict(self)

@dataclass(frozen=True)
class RawOfficialResource: candidate:ResourceCandidate; body:bytes; mime_type:str; status_code:int=200
@dataclass(frozen=True)
class ValidationResult: accepted:bool; reason:str|None=None; warnings:tuple[str,...]=()
@dataclass(frozen=True)
class ParsedOfficialResource: resource:CnilResource; extracted_text:str=""
