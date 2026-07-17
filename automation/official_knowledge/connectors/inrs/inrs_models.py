from dataclasses import asdict,dataclass
from enum import StrEnum

from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_provenance import Provenance

class ResourceFamily(StrEnum):
 BROCHURE="brochure"; PRACTICAL_SHEET="practical_sheet"; DOSSIER="dossier"; NEWS="news"
 QUESTION_ANSWER="question_answer"; TOOL="tool"; DOCUMENTARY_DATABASE="documentary_database"
 VIDEO="video"; PODCAST="podcast"; POSTER="poster"; PDF_DOCUMENT="pdf_document"

class EvidenceStatus(StrEnum):
 OFFICIALLY_OBSERVED="officially_observed"; NOT_IDENTIFIED_IN_LIMITED_REVIEW="not_identified_in_limited_review"
 OBSERVED_NOT_VALIDATED="observed_not_validated"; LEGAL_REVIEW_REQUIRED="legal_review_required"

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
 def __post_init__(self):
  if not self.reference or not self.title:raise ValueError("reference and title required")
 def to_dict(self):return asdict(self)
 def fingerprint(self)->str:return fingerprint_metadata((self.reference,self.title,self.family.value,self.publication_date or "",self.version_note or ""))
 def citation(self,canonical_url:str)->Citation:return Citation(canonical_url,self.title,"INRS",self.publication_date,self.version_note,"official_prevention_guidance","DOCUMENT_SPECIFIC","high")
 def provenance(self,canonical_url:str)->Provenance:return Provenance("inrs",canonical_url,None,self.fingerprint())
