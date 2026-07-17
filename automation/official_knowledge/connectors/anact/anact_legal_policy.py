"""Conservative legal classification from the limited official audit."""
from dataclasses import dataclass
from enum import StrEnum

from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId

class LegalStatus(StrEnum):EXPLICITLY_ALLOWED="explicitly_allowed"; ALLOWED_WITH_CONDITIONS="allowed_with_conditions"; NOT_DOCUMENTED="not_documented"; UNCERTAIN="uncertain"; HUMAN_REVIEW="human_review"; NOT_USABLE="not_usable"

@dataclass(frozen=True)
class LegalPolicy:
 legal_url:str;privacy_url:str;accessibility_url:str;reuse_status:LegalStatus
 license_id:LicenseId=LicenseId.DOCUMENT_SPECIFIC;document_policy:DocumentPolicy=DocumentPolicy.METADATA_ONLY
 cache_allowed:bool=False;fulltext_allowed:bool=False;excerpts_allowed:bool=False;human_review_required:bool=True
 def __post_init__(self):
  if not all(url.startswith("https://www.anact.fr/") for url in (self.legal_url,self.privacy_url,self.accessibility_url)):raise ValueError("official legal URLs required")
  if self.license_id is not LicenseId.DOCUMENT_SPECIFIC or self.document_policy is not DocumentPolicy.METADATA_ONLY:raise ValueError("LOT 1 legal policy must remain conservative")

ANACT_LEGAL_POLICY=LegalPolicy("https://www.anact.fr/mentions-legales","https://www.anact.fr/politique-generale-de-protection-des-donnees-caractere-personnel","https://www.anact.fr/accessibilite",LegalStatus.HUMAN_REVIEW)
