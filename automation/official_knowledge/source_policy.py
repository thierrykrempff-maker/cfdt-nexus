"""HTTPS allow-list policy with SSRF-oriented URL validation."""
from __future__ import annotations
from dataclasses import dataclass
import ipaddress
from urllib.parse import urlsplit

@dataclass(frozen=True)
class AccessPolicy:
    official_domains: tuple[str,...]; allow_subdomains: bool=True; https_only: bool=True
    max_download_bytes: int=10_000_000; allowed_mime_types: tuple[str,...]=("application/json","text/html","application/pdf","text/plain")

def validate_url(url: str, policy: AccessPolicy) -> str:
    parsed=urlsplit(url)
    if parsed.scheme not in ({"https"} if policy.https_only else {"https","http"}): raise ValueError("SCHEME_REFUSED")
    if parsed.username or parsed.password: raise ValueError("URL_CREDENTIALS_REFUSED")
    host=(parsed.hostname or "").rstrip(".").casefold()
    if host in {"localhost","localhost.localdomain"}: raise ValueError("LOCALHOST_REFUSED")
    try:
        ip=ipaddress.ip_address(host)
        if not ip.is_global: raise ValueError("NON_PUBLIC_IP_REFUSED")
    except ValueError as exc:
        if str(exc)=="NON_PUBLIC_IP_REFUSED": raise
    allowed=any(host==d.casefold() or (policy.allow_subdomains and host.endswith("."+d.casefold())) for d in policy.official_domains)
    if not allowed: raise ValueError("DOMAIN_REFUSED")
    return url

def validate_redirect(original: str,target: str,policy:AccessPolicy)->str:
    validate_url(original,policy); return validate_url(target,policy)
def validate_payload(size:int,mime_type:str,policy:AccessPolicy)->None:
    if size>policy.max_download_bytes: raise ValueError("DOWNLOAD_TOO_LARGE")
    if mime_type.split(";",1)[0].strip().casefold() not in policy.allowed_mime_types: raise ValueError("MIME_REFUSED")
