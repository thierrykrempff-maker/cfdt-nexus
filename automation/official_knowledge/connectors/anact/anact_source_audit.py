"""Versioned facts observed during the limited official ANACT source audit."""
from dataclasses import dataclass
from enum import StrEnum

class EvidenceLevel(StrEnum):CONFIRMED="confirmed"; PROBABLE="probable"; NOT_CONFIRMED="not_confirmed"; REJECTED="rejected"
class AuditDecision(StrEnum):RETAINED="retained"; DEFERRED="deferred"; REJECTED="rejected"

@dataclass(frozen=True)
class SourceAuditRecord:
 mechanism:str;url:str|None;evidence:EvidenceLevel;decision:AuditDecision
 observed_on:str;http_status:int|None=None;mime_type:str|None=None;structure:str=""
 stable_identifiers:bool|None=None;metadata_quality:str="unknown";pagination:str="not_observed"
 update_hint:str|None=None;etag_observed:bool=False;last_modified_observed:bool=False;limitations:tuple[str,...]=()
 def __post_init__(self):
  if not self.mechanism or not self.observed_on:raise ValueError("audit identity required")
  if self.url is not None and not self.url.startswith("https://www.anact.fr"):raise ValueError("non-official ANACT audit domain")
  if self.evidence is EvidenceLevel.CONFIRMED and (self.url is None or self.http_status is None):raise ValueError("confirmed evidence requires observed response")

AUDIT_RECORDS=(
 SourceAuditRecord("homepage","https://www.anact.fr/",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","Drupal 10 HTML, French content language",True,"headers_only",limitations=("page payload metadata not retained",)),
 SourceAuditRecord("robots_txt","https://www.anact.fr/robots.txt",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/plain","Drupal robots rules",False,"technical",etag_observed=True,last_modified_observed=True,limitations=("faceted and paginated lists disallowed","search paths disallowed")),
 SourceAuditRecord("xml_sitemap","https://www.anact.fr/sitemap.xml",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/xml; charset=utf-8","XML urlset with loc, lastmod, changefreq and optional priority",True,"high","not_applicable","daily",True,True),
 SourceAuditRecord("themes","https://www.anact.fr/themes",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","official thematic landing page",True,"headers_and_sitemap","deferred",last_modified_observed=True),
 SourceAuditRecord("regions","https://www.anact.fr/regions",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","central official regional network landing page",True,"headers_and_sitemap","deferred",last_modified_observed=True),
 SourceAuditRecord("aract_grand_est","https://www.anact.fr/grand-est",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","regional page integrated in national Drupal site",True,"headers_and_sitemap","deferred",last_modified_observed=False),
 SourceAuditRecord("legal_notices","https://www.anact.fr/mentions-legales",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","official legal page; substantive reuse terms require human review",True,"headers_only",last_modified_observed=True,limitations=("no general reuse licence established",)),
 SourceAuditRecord("privacy","https://www.anact.fr/politique-generale-de-protection-des-donnees-caractere-personnel",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","official personal-data policy page",True,"headers_and_sitemap",last_modified_observed=True),
 SourceAuditRecord("accessibility","https://www.anact.fr/accessibilite",EvidenceLevel.CONFIRMED,AuditDecision.RETAINED,"2026-07-17",200,"text/html; charset=UTF-8","official accessibility page",True,"headers_and_sitemap",last_modified_observed=True),
 SourceAuditRecord("internal_search",None,EvidenceLevel.REJECTED,AuditDecision.REJECTED,"2026-07-17",structure="robots.txt disallows search paths",limitations=("must not be used for automated discovery",)),
 SourceAuditRecord("faceted_pagination",None,EvidenceLevel.REJECTED,AuditDecision.REJECTED,"2026-07-17",structure="robots.txt disallows query variants for list pages",limitations=("must not be crawled",)),
 SourceAuditRecord("rss_atom",None,EvidenceLevel.NOT_CONFIRMED,AuditDecision.DEFERRED,"2026-07-17",limitations=("no official feed observed in limited audit",)),
 SourceAuditRecord("public_api",None,EvidenceLevel.NOT_CONFIRMED,AuditDecision.DEFERRED,"2026-07-17",limitations=("no official API documentation observed",)),
 SourceAuditRecord("structured_metadata",None,EvidenceLevel.NOT_CONFIRMED,AuditDecision.DEFERRED,"2026-07-17",limitations=("JSON-LD, Open Graph and canonical markup not validated",)),
 SourceAuditRecord("downloadable_documents",None,EvidenceLevel.NOT_CONFIRMED,AuditDecision.DEFERRED,"2026-07-17",limitations=("no document downloaded or retained",)),
)
AUDIT_BY_MECHANISM={record.mechanism:record for record in AUDIT_RECORDS}
