"""Models for the bounded ANACT sitemap transport; never stores page content."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class FetchStatus(StrEnum):FETCHED="fetched"; NOT_MODIFIED="not_modified"; INVALID="invalid"; TEMPORARILY_UNAVAILABLE="temporarily_unavailable"; ACCESS_DENIED="access_denied"; NETWORK_ERROR="network_error"
class SitemapKind(StrEnum):URLSET="urlset"; SITEMAP_INDEX="sitemapindex"
class FilterDecision(StrEnum):ACCEPTED="accepted"; REJECTED="rejected"

@dataclass(frozen=True)
class TransportLimits:
 timeout_seconds:float=10;max_redirects:int=2;max_response_bytes:int=2_000_000;max_urls:int=5_000;max_sub_sitemaps:int=10;max_depth:int=1
 def __post_init__(self):
  if self.timeout_seconds<=0 or min(self.max_redirects,self.max_response_bytes,self.max_urls,self.max_sub_sitemaps,self.max_depth)<0:raise ValueError("invalid transport limits")

@dataclass(frozen=True)
class ConditionalState:etag:str|None=None;last_modified:str|None=None

@dataclass(frozen=True)
class HttpRequest:
 url:str;headers:tuple[tuple[str,str],...];timeout_seconds:float;max_redirects:int;max_response_bytes:int

@dataclass(frozen=True)
class HttpResponse:
 status:int;url:str;headers:tuple[tuple[str,str],...];body:bytes=b""
 def header(self,name:str)->str|None:
  target=name.lower();return next((value for key,value in self.headers if key.lower()==target),None)

@dataclass(frozen=True)
class SitemapCandidate:
 original_url:str;normalized_url:str|None;domain:str|None;path:str|None;entry_type:str
 lastmod_raw:str|None;lastmod_normalized:str|None;changefreq_raw:str|None
 family_hint:str|None;scope:str|None;aract_id:str|None;discovered_at:datetime;collected_at:datetime
 sitemap_url:str;etag:str|None;http_last_modified:str|None;validation_status:str
 decision:FilterDecision;rejection_reason:str|None;fingerprint:str;synthetic_only:bool=False;fulltext:str|None=None

@dataclass(frozen=True)
class SitemapDiagnostics:
 connector_id:str;source_url:str;started_at:datetime;finished_at:datetime;http_status:int|None
 mime_type:str|None;bytes_received:int;etag:str|None;last_modified:str|None
 xml_entries:int;valid_entries:int;duplicates:int;rejected_entries:int;rejection_reasons:tuple[tuple[str,int],...]
 limit_reached:bool;status:FetchStatus;error_code:str|None=None

@dataclass(frozen=True)
class SitemapInspectionResult:
 status:FetchStatus;kind:SitemapKind|None;candidates:tuple[SitemapCandidate,...]
 conditional_state:ConditionalState;diagnostics:SitemapDiagnostics
