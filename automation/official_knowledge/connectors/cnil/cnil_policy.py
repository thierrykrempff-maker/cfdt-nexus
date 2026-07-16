"""Allow-list selection policy for a future CNIL connector."""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlsplit,parse_qs
from automation.official_knowledge.source_policy import AccessPolicy,validate_url
from .cnil_catalog import THEME_PRIORITIES
from .cnil_models import ResourceCandidate,ValidationResult

@dataclass(frozen=True)
class CnilSelectionPolicy:
 allowed_domains:tuple[str,...]=("cnil.fr","linc.cnil.fr","data.gouv.fr","legifrance.gouv.fr")
 allowed_resource_types:tuple[str,...]=("web_guidance","news","press_release","guide","report","deliberation","sanction","faq","definition","downloadable_document","open_dataset")
 allowed_mime_types:tuple[str,...]=("text/html","application/pdf","application/json","text/csv")
 max_size_bytes:int=5_000_000; language:str="fr"; max_navigation_depth:int=1
 allowed_path_prefixes:tuple[str,...]=("/fr/","/organizations/cnil/","/cnil/","/sites/")

def validate_candidate(candidate:ResourceCandidate,policy:CnilSelectionPolicy=CnilSelectionPolicy(),*,size_bytes:int=0,license_status:str="pending")->ValidationResult:
 try:validate_url(candidate.canonical_uri,AccessPolicy(policy.allowed_domains,allowed_mime_types=policy.allowed_mime_types,max_download_bytes=policy.max_size_bytes))
 except ValueError as exc:return ValidationResult(False,str(exc))
 parsed=urlsplit(candidate.canonical_uri);path=parsed.path.casefold();query=parse_qs(parsed.query)
 if not any(path.startswith(p.casefold()) for p in policy.allowed_path_prefixes):return ValidationResult(False,"PATH_REFUSED")
 if any(x in path for x in ("/plainte","/demarche","/formulaire","/mon-compte","/services")):return ValidationResult(False,"TRANSACTIONAL_RESOURCE_REFUSED")
 if any(k.casefold() in {"email","token","name","person","user"} for k in query):return ValidationResult(False,"SENSITIVE_PARAMETERS_REFUSED")
 if candidate.resource_type not in policy.allowed_resource_types:return ValidationResult(False,"RESOURCE_TYPE_REFUSED")
 if candidate.content_format not in policy.allowed_mime_types:return ValidationResult(False,"MIME_REFUSED")
 if size_bytes>policy.max_size_bytes:return ValidationResult(False,"RESOURCE_TOO_LARGE")
 allowed_themes=set().union(*THEME_PRIORITIES.values())
 if candidate.theme_tags and not set(candidate.theme_tags)&allowed_themes:return ValidationResult(False,"THEME_REFUSED")
 if license_status in {"pending","restricted","prohibited"}:return ValidationResult(False,"LICENSE_NOT_APPROVED")
 return ValidationResult(True)
