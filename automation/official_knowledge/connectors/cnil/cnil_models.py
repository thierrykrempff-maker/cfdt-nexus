"""Synthetic-safe CNIL resource and connector contracts."""
from __future__ import annotations
from dataclasses import asdict,dataclass,field
from datetime import date
from typing import Any
import uuid
from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_provenance import Provenance
from automation.official_knowledge.fingerprints import canonicalize_uri

RESOURCE_TYPES={"web_guidance","news","press_release","guide","report","deliberation","sanction","faq","definition","downloadable_document","open_dataset","video_metadata","unknown"}

def stable_resource_id(uri:str)->str:return str(uuid.uuid5(uuid.NAMESPACE_URL,"cfdt-nexus:cnil:"+canonicalize_uri(uri)))

@dataclass(frozen=True)
class ResourceCandidate:
 canonical_uri:str; resource_type:str="unknown"; title:str=""; theme_tags:tuple[str,...]=(); audience_tags:tuple[str,...]=(); retrieval_mode:str="targeted_page"; content_format:str="text/html"
 def __post_init__(self):
  if self.resource_type not in RESOURCE_TYPES:raise ValueError("invalid resource_type")
 def to_platform_citation(self)->Citation:
  return Citation(self.canonical_uri,self.title,None,None,None,"official_guidance","CC_BY_ND","very_low")
 def to_platform_provenance(self)->Provenance:
  return Provenance("cnil",self.canonical_uri,None,self.platform_fingerprint())
 def platform_fingerprint(self)->str:
  return fingerprint_metadata((self.canonical_uri,self.resource_type,self.title,*self.theme_tags,*self.audience_tags))

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
 def to_platform_citation(self)->Citation:
  return Citation(self.canonical_uri,self.title,None,self.publication_date.isoformat() if self.publication_date else None,self.schema_version,self.authority_level,self.license_id or "UNKNOWN","very_low")
 def to_platform_provenance(self)->Provenance:
  digest=self.content_sha256 or fingerprint_metadata((self.source_id,self.canonical_uri,self.title,self.schema_version))
  return Provenance(self.source_id,self.canonical_uri,None,digest)

@dataclass(frozen=True)
class RawOfficialResource: candidate:ResourceCandidate; body:bytes; mime_type:str; status_code:int=200
@dataclass(frozen=True)
class ValidationResult: accepted:bool; reason:str|None=None; warnings:tuple[str,...]=()
@dataclass(frozen=True)
class ParsedOfficialResource: resource:CnilResource; extracted_text:str=""
