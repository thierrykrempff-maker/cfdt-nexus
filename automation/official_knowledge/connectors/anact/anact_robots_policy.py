"""Fixed LOT 1 robots policy and strict ANACT URL validation."""
from dataclasses import dataclass
from urllib.parse import urlsplit,urlunsplit

from .anact_source_registry import REGION_BY_ID

ALLOWED_HOSTS=frozenset({"www.anact.fr","anact.fr"})
FORBIDDEN_PATH_PREFIXES=("/search/","/recherche","/admin/","/user/","/comment/reply/","/filter/tips","/media/oembed")
FACETED_LIST_PATHS=frozenset({"/actualites","/evenements","/realisations-et-projets","/ressources","/services"})
REJECTED_EXTENSIONS=(".pdf",".doc",".docx",".zip",".exe")

@dataclass(frozen=True)
class UrlPolicyResult:
 allowed:bool;normalized_url:str|None;reason:str|None;domain:str|None;path:str|None;scope:str|None;aract_id:str|None

def validate_candidate_url(raw_url:str)->UrlPolicyResult:
 try:parts=urlsplit(raw_url)
 except ValueError:return UrlPolicyResult(False,None,"invalid_url",None,None,None,None)
 host=(parts.hostname or "").lower();path=parts.path or "/"
 if parts.scheme!="https":return UrlPolicyResult(False,None,"https_required",host or None,path,None,None)
 if parts.username or parts.password:return UrlPolicyResult(False,None,"embedded_credentials",host or None,path,None,None)
 if host not in ALLOWED_HOSTS:return UrlPolicyResult(False,None,"domain_not_allowed",host or None,path,None,None)
 lowered=path.lower()
 if any(lowered.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES):return UrlPolicyResult(False,None,"robots_forbidden_path",host,path,None,None)
 if parts.query and lowered in FACETED_LIST_PATHS:return UrlPolicyResult(False,None,"faceted_pagination_forbidden",host,path,None,None)
 if parts.query:return UrlPolicyResult(False,None,"query_parameters_not_authorized",host,path,None,None)
 if any(lowered.endswith(extension) for extension in REJECTED_EXTENSIONS):return UrlPolicyResult(False,None,"downloadable_document_forbidden",host,path,None,None)
 normalized=urlunsplit(("https",host,path,"",""))
 aract_id=next((region_id for region_id,entity in REGION_BY_ID.items() if urlsplit(entity.official_url).path.rstrip("/")==path.rstrip("/")),None)
 return UrlPolicyResult(True,normalized,None,host,path,"regional" if aract_id else "national",aract_id)

def validate_transport_url(url:str)->None:
 result=validate_candidate_url(url)
 if not result.allowed:raise ValueError(result.reason or "transport URL rejected")
