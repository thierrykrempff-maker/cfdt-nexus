"""Immutable contracts for future DREETS Grand Est resources."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_provenance import Provenance

CONTENT_CATEGORIES=frozenset({"guide","faq","actualité","instruction","circulaire","fiche","publication","dossier","communiqué","formulaire","modèle"})
AUTHORITY_LEVELS=frozenset({"official_guidance","official_practical_information","official_regulation","primary_law_reference","unknown"})
VALIDITY_LEVELS=frozenset({"current_until_review","time_limited","historical","unknown"})
REVISION_FREQUENCIES=frozenset({"manual","monthly","quarterly","semiannual","annual","on_official_change","unknown"})
CONFIDENCE_LEVELS=frozenset({"very_high","high","medium","low","very_low"})
CITATION_LEVELS=frozenset({"metadata_only","short_excerpt_if_authorized","official_reference_required","full_citation_required"})

@dataclass(frozen=True)
class DreetsDocumentType:
 category:str;authority_level:str;document_policy_id:str;license_id:str="UNKNOWN"
 validity_level:str="unknown";revision_frequency:str="unknown";confidence_level:str="very_low"
 citation_level:str="metadata_only";full_text_allowed:bool=False;cache_allowed:bool=False;index_level:str="METADATA_ONLY"
 require_provenance:bool=True
 def __post_init__(self):
  if self.category not in CONTENT_CATEGORIES:raise ValueError("invalid category")
  if self.authority_level not in AUTHORITY_LEVELS:raise ValueError("invalid authority")
  if self.validity_level not in VALIDITY_LEVELS or self.revision_frequency not in REVISION_FREQUENCIES:raise ValueError("invalid lifecycle")
  if self.confidence_level not in CONFIDENCE_LEVELS or self.citation_level not in CITATION_LEVELS:raise ValueError("invalid confidence or citation")
  if not self.require_provenance:raise ValueError("provenance is mandatory")
  if self.license_id=="UNKNOWN" and (self.full_text_allowed or self.cache_allowed or self.index_level!="METADATA_ONLY"):raise ValueError("unknown license is metadata only")
 def to_dict(self):return asdict(self)
 def to_platform_policy(self)->DocumentPolicy:
  if self.full_text_allowed:return DocumentPolicy.FULLTEXT_ALLOWED
  return DocumentPolicy.METADATA_ONLY
 def to_platform_license(self)->LicenseId:
  aliases={"UNKNOWN":LicenseId.UNKNOWN,"DOCUMENT_SPECIFIC_REVIEW":LicenseId.DOCUMENT_SPECIFIC}
  return aliases.get(self.license_id,LicenseId(self.license_id))

@dataclass(frozen=True)
class DreetsResourceCandidate:
 source_id:str;canonical_uri:str;title:str;category:str;domain_tags:tuple[str,...]
 authority_level:str="official_guidance";license_id:str="UNKNOWN";access_review_status:str="pending_official_review"
 def __post_init__(self):
  if self.source_id!="dreets_grand_est":raise ValueError("invalid source")
  if self.category not in CONTENT_CATEGORIES:raise ValueError("invalid category")
  if self.canonical_uri and (len(self.canonical_uri)>1 and self.canonical_uri[1]==":" or self.canonical_uri.startswith(("/home/","/Users/"))):raise ValueError("absolute path refused")
 def to_platform_citation(self)->Citation:
  return Citation(self.canonical_uri,self.title,None,None,None,self.authority_level,self.license_id,"very_low")
 def to_platform_provenance(self)->Provenance:
  digest=fingerprint_metadata((self.source_id,self.canonical_uri,self.title,self.category,*self.domain_tags))
  return Provenance(self.source_id,self.canonical_uri,None,digest)

@dataclass(frozen=True)
class ClassificationResult:
 domains:tuple[str,...];category:str;confidence_level:str;citation_level:str
 requires_official_text_check:bool;warnings:tuple[str,...]=()
