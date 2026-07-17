"""Explicitly enabled, read-only transport limited to the audited ANACT sitemap."""
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import StrEnum
from typing import Callable,Protocol
import ssl
import urllib.error
import urllib.request

from .anact_catalog import CONFIRMED_ENTRY_POINTS
from .anact_robots_policy import ALLOWED_HOSTS,validate_transport_url
from .anact_sitemap_parser import SitemapParseError,parse_sitemap
from .anact_transport_models import ConditionalState,FetchStatus,HttpRequest,HttpResponse,SitemapDiagnostics,SitemapInspectionResult,TransportLimits

SITEMAP_URL=CONFIRMED_ENTRY_POINTS["sitemap"]
USER_AGENT="CFDT-Nexus-ANACT-Sitemap/1.0 (+metadata-only; contact=repository-maintainer)"
ACCEPTED_MIME_TYPES=frozenset({"application/xml","text/xml","application/sitemap+xml"})

class TransportErrorCode(StrEnum):DISABLED="transport_disabled"; DOMAIN="domain_not_allowed"; REDIRECT="redirect_not_allowed"; HTTP="http_error"; TIMEOUT="timeout"; TLS="tls_error"; NETWORK="network_error"; MIME="unexpected_mime_type"; SIZE="response_too_large"; XML="invalid_xml"; HTML="invalid_html"
class AnactTransportError(RuntimeError):
 def __init__(self,code:TransportErrorCode,message:str,status:int|None=None):self.code=code;self.status=status;super().__init__(message)

class HttpAdapter(Protocol):
 def send(self,request:HttpRequest)->HttpResponse:...

class _RestrictedRedirectHandler(urllib.request.HTTPRedirectHandler):
 def __init__(self,max_redirects:int):self.max_redirects=max_redirects;self.count=0
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  self.count+=1
  if self.count>self.max_redirects:raise AnactTransportError(TransportErrorCode.REDIRECT,"redirect_limit_exceeded",code)
  try:validate_transport_url(newurl)
  except ValueError as error:raise AnactTransportError(TransportErrorCode.REDIRECT,str(error),code) from error
  return super().redirect_request(req,fp,code,msg,headers,newurl)

class UrllibHttpAdapter:
 def send(self,request:HttpRequest)->HttpResponse:
  validate_transport_url(request.url)
  redirect_handler=_RestrictedRedirectHandler(request.max_redirects)
  opener=urllib.request.build_opener(redirect_handler,urllib.request.HTTPSHandler(context=ssl.create_default_context()))
  raw_request=urllib.request.Request(request.url,headers=dict(request.headers),method="GET")
  try:
   with opener.open(raw_request,timeout=request.timeout_seconds) as response:
    body=response.read(request.max_response_bytes+1)
    if len(body)>request.max_response_bytes:raise AnactTransportError(TransportErrorCode.SIZE,"response_too_large",response.status)
    return HttpResponse(response.status,response.geturl(),tuple(response.headers.items()),body)
  except urllib.error.HTTPError as error:
   if error.code==304:return HttpResponse(304,error.geturl(),tuple(error.headers.items()),b"")
   return HttpResponse(error.code,error.geturl(),tuple(error.headers.items()),b"")
  except TimeoutError as error:raise AnactTransportError(TransportErrorCode.TIMEOUT,"network_timeout") from error
  except ssl.SSLError as error:raise AnactTransportError(TransportErrorCode.TLS,"tls_error") from error
  except urllib.error.URLError as error:raise AnactTransportError(TransportErrorCode.NETWORK,"network_error") from error

@dataclass(frozen=True)
class SitemapTransportConfig:
 enabled:bool=False;limits:TransportLimits=TransportLimits()

class AnactSitemapTransport:
 def __init__(self,adapter:HttpAdapter,config:SitemapTransportConfig=SitemapTransportConfig(),clock:Callable[[],datetime]|None=None):self.adapter=adapter;self.config=config;self.clock=clock or (lambda:datetime.now(timezone.utc))
 def build_request(self,state:ConditionalState=ConditionalState())->HttpRequest:
  validate_transport_url(SITEMAP_URL)
  headers=[("Accept","application/xml, text/xml;q=0.9"),("User-Agent",USER_AGENT)]
  if state.etag:headers.append(("If-None-Match",state.etag))
  if state.last_modified:headers.append(("If-Modified-Since",state.last_modified))
  return HttpRequest(SITEMAP_URL,tuple(headers),self.config.limits.timeout_seconds,self.config.limits.max_redirects,self.config.limits.max_response_bytes)
 def inspect(self,state:ConditionalState=ConditionalState())->SitemapInspectionResult:
  if not self.config.enabled:raise AnactTransportError(TransportErrorCode.DISABLED,"transport_disabled")
  started=self.clock();request=self.build_request(state)
  try:response=self.adapter.send(request)
  except AnactTransportError:raise
  try:validate_transport_url(response.url)
  except ValueError as error:raise AnactTransportError(TransportErrorCode.REDIRECT,str(error),response.status) from error
  mime=(response.header("Content-Type") or "").split(";",1)[0].strip().lower() or None
  etag=response.header("ETag") or state.etag;last_modified=response.header("Last-Modified") or state.last_modified
  next_state=ConditionalState(etag,last_modified)
  if response.status==304:return self._result(FetchStatus.NOT_MODIFIED,None,(),next_state,started,response,mime)
  if response.status in {401,403}:return self._result(FetchStatus.ACCESS_DENIED,None,(),next_state,started,response,mime,error="access_denied")
  if response.status==404:return self._result(FetchStatus.INVALID,None,(),next_state,started,response,mime,error="not_found")
  if response.status==429 or 500<=response.status<=599:return self._result(FetchStatus.TEMPORARILY_UNAVAILABLE,None,(),next_state,started,response,mime,error=f"http_{response.status}")
  if response.status in {301,302}:raise AnactTransportError(TransportErrorCode.REDIRECT,"unresolved_redirect",response.status)
  if response.status!=200:raise AnactTransportError(TransportErrorCode.HTTP,f"unexpected_http_{response.status}",response.status)
  if mime not in ACCEPTED_MIME_TYPES:raise AnactTransportError(TransportErrorCode.MIME,"unexpected_mime_type",response.status)
  if len(response.body)>self.config.limits.max_response_bytes:raise AnactTransportError(TransportErrorCode.SIZE,"response_too_large",response.status)
  try:kind,candidates,counts=parse_sitemap(response.body,sitemap_url=SITEMAP_URL,state=next_state,limits=self.config.limits,discovered_at=started,collected_at=self.clock())
  except SitemapParseError as error:raise AnactTransportError(TransportErrorCode.XML,str(error),response.status) from error
  return self._result(FetchStatus.FETCHED,kind,candidates,next_state,started,response,mime,counts)
 def _result(self,status,kind,candidates,state,started,response,mime,counts=None,error=None):
  counts=counts or {};finished=self.clock()
  diagnostics=SitemapDiagnostics("anact",SITEMAP_URL,started,finished,response.status,mime,len(response.body),state.etag,state.last_modified,int(counts.get("xml_entries",0)),sum(item.decision.value=="accepted" for item in candidates),int(counts.get("duplicates",0)),int(counts.get("rejected",0)),tuple(counts.get("reasons",())),bool(counts.get("limit_reached",False)),status,error)
  return SitemapInspectionResult(status,kind,tuple(candidates),state,diagnostics)
