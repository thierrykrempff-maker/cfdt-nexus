"""Declarative CARSAT document models containing metadata only."""
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from automation.connector_platform.connector_citation import Citation
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_fingerprint import fingerprint_metadata
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_provenance import Provenance

class CarsatMission(StrEnum):
 OCCUPATIONAL_RISK_PREVENTION="occupational_risk_prevention"
 RETIREMENT="retirement"
 SOCIAL_SERVICE="social_service"
 WORK_ACCIDENT_PRICING="work_accident_pricing"
 HEALTH_AT_WORK="health_at_work"

class CarsatDocumentFamily(StrEnum):
 PREVENTION_GUIDE="prevention_guide"; PRACTICAL_SHEET="practical_sheet"
 TECHNICAL_RECOMMENDATION="technical_recommendation"; REGIONAL_PUBLICATION="regional_publication"
 RETIREMENT_INFORMATION="retirement_information"; SOCIAL_SERVICE_INFORMATION="social_service_information"
 WORK_ACCIDENT_PRICING_INFORMATION="work_accident_pricing_information"
 FORM="form"; FAQ="faq"; NEWS="news"; TOOL="tool"; OTHER="other"

class AccessReviewStatus(StrEnum):
 PENDING_OFFICIAL_REVIEW="pending_official_review"

@dataclass(frozen=True)
class AccessPossibility:
 mechanism:str;status:AccessReviewStatus=AccessReviewStatus.PENDING_OFFICIAL_REVIEW
 operational:bool=False;notes:str=""
 def __post_init__(self):
  if not self.mechanism or self.operational:raise ValueError("LOT 0 access cannot be operational")

@dataclass(frozen=True)
class CarsatDocumentIdentity:
 reference:str;title:str;family:CarsatDocumentFamily;mission:CarsatMission
 publication_date:str|None=None;version:str|None=None
 def __post_init__(self):
  if not self.reference or not self.title:raise ValueError("reference and title required")
 def to_dict(self)->dict[str,Any]:
  return {"reference":self.reference,"title":self.title,"family":self.family.value,"mission":self.mission.value,"publication_date":self.publication_date,"version":self.version}
 @classmethod
 def from_dict(cls,value:dict[str,Any])->"CarsatDocumentIdentity":
  if not {"reference","title","family","mission"}<=value.keys():raise ValueError("missing document identity field")
  return cls(str(value["reference"]),str(value["title"]),CarsatDocumentFamily(value["family"]),CarsatMission(value["mission"]),value.get("publication_date"),value.get("version"))
 def fingerprint(self)->str:
  return fingerprint_metadata((self.reference,self.title,self.family.value,self.mission.value,self.publication_date or "",self.version or ""))
 def platform_policy(self)->DocumentPolicy:return DocumentPolicy.METADATA_ONLY
 def platform_license(self)->LicenseId:return LicenseId.DOCUMENT_SPECIFIC
 def citation(self,canonical_url:str)->Citation:
  return Citation(canonical_url,self.title,"CARSAT",self.publication_date,self.version,"institutional_information",self.platform_license().value,"medium")
 def provenance(self,canonical_url:str)->Provenance:return Provenance("carsat",canonical_url,None,self.fingerprint())
