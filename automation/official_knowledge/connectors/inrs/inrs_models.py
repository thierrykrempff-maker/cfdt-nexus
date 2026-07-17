from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_provenance import Provenance

class ResourceFamily(StrEnum):
 BROCHURE="brochure"; PRACTICAL_SHEET="practical_sheet"; DOSSIER="dossier"; NEWS="news"
 QUESTION_ANSWER="question_answer"; TOOL="tool"; DOCUMENTARY_DATABASE="documentary_database"
 VIDEO="video"; PODCAST="podcast"; POSTER="poster"; PDF_DOCUMENT="pdf_document"

class EvidenceStatus(StrEnum):
 OFFICIALLY_OBSERVED="officially_observed"; NOT_IDENTIFIED_IN_LIMITED_REVIEW="not_identified_in_limited_review"
 OBSERVED_NOT_VALIDATED="observed_not_validated"; LEGAL_REVIEW_REQUIRED="legal_review_required"

class InrsDocumentType(StrEnum):
 ED="ed"; TJ="tj"; AD="ad"; AR="ar"; BROCHURE="brochure"; FICHE="fiche"
 DOSSIER="dossier"; FAQ="faq"; OUTIL="outil"; PUBLICATION="publication"; AUTRE="autre"

@dataclass(frozen=True)
class AccessEvidence:
 mechanism:str;status:EvidenceStatus;operational:bool=False;notes:str=""
 def __post_init__(self):
  if not self.mechanism or self.operational:raise ValueError("LOT 0 evidence cannot enable access")

@dataclass(frozen=True)
class FamilyProfile:
 family:ResourceFamily;jurist_interest:str;payroll_interest:str;social_protection_interest:str
 cssct_interest:str;hse_interest:str;nexus_interest:str;priority:int
 def __post_init__(self):
  allowed={"none","low","medium","high","very_high"}
  if not {self.jurist_interest,self.payroll_interest,self.social_protection_interest,self.cssct_interest,self.hse_interest,self.nexus_interest}<=allowed:raise ValueError("invalid interest")
  if not 1<=self.priority<=5:raise ValueError("invalid priority")

@dataclass(frozen=True)
class InrsDocumentIdentity:
 reference:str;title:str;family:ResourceFamily;publication_date:str|None=None;version_note:str|None=None
 document_type:InrsDocumentType=InrsDocumentType.AUTRE
 def __post_init__(self):
  if not self.reference or not self.title:raise ValueError("reference and title required")
 def to_dict(self)->dict[str,Any]:
  return {"reference":self.reference,"title":self.title,"family":self.family.value,"publication_date":self.publication_date,"version_note":self.version_note,"document_type":self.document_type.value}
 @classmethod
 def from_dict(cls,value:dict[str,Any])->"InrsDocumentIdentity":
  required={"reference","title","family"}
  if not required<=value.keys():raise ValueError("missing document identity field")
  return cls(str(value["reference"]),str(value["title"]),ResourceFamily(value["family"]),value.get("publication_date"),value.get("version_note"),InrsDocumentType(value.get("document_type","autre")))
 def fingerprint(self)->str:return fingerprint_metadata((self.reference,self.title,self.family.value,self.publication_date or "",self.version_note or "",self.document_type.value))
 def platform_policy(self)->DocumentPolicy:return DocumentPolicy.METADATA_ONLY
 def platform_license(self)->LicenseId:return LicenseId.DOCUMENT_SPECIFIC
 def citation(self,canonical_url:str)->Citation:return Citation(canonical_url,self.title,"INRS",self.publication_date,self.version_note,"official_prevention_guidance",self.platform_license().value,"high")
 def provenance(self,canonical_url:str)->Provenance:return Provenance("inrs",canonical_url,None,self.fingerprint())
