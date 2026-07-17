"""Strict deterministic offline parser for ANACT sitemap metadata."""
from collections import Counter
from datetime import datetime,timezone
import xml.etree.ElementTree as ET

from automation.connector_platform.connector_fingerprint import fingerprint_metadata

from .anact_robots_policy import validate_candidate_url
from .anact_transport_models import ConditionalState,FilterDecision,SitemapCandidate,SitemapKind,TransportLimits

SITEMAP_NAMESPACE="http://www.sitemaps.org/schemas/sitemap/0.9"

class SitemapParseError(ValueError):pass

def _local(tag:str)->str:return tag.rsplit("}",1)[-1]
def _text(element:ET.Element,name:str)->str|None:
 child=next((item for item in element if _local(item.tag)==name),None)
 return child.text.strip() if child is not None and child.text else None
def _normalize_date(value:str|None)->str|None:
 if not value:return None
 try:return datetime.fromisoformat(value.replace("Z","+00:00")).isoformat()
 except ValueError:return None
def _family_hint(path:str|None)->str|None:
 value=(path or "").lower()
 rules=(("outil","tools"),("autodiagnostic","tools"),("guide","guides"),("fiche","practical_sheets"),("webinaire","events"),("actualite","news"))
 return next((family for token,family in rules if token in value),None)

def parse_sitemap(xml_body:bytes,*,sitemap_url:str,state:ConditionalState,limits:TransportLimits,discovered_at:datetime,collected_at:datetime)->tuple[SitemapKind,tuple[SitemapCandidate,...],dict[str,int|bool]]:
 if len(xml_body)>limits.max_response_bytes:raise SitemapParseError("response_too_large")
 upper=xml_body[:1024].upper()
 if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:raise SitemapParseError("unsafe_xml_declaration")
 try:root=ET.fromstring(xml_body)
 except ET.ParseError as error:raise SitemapParseError("malformed_xml") from error
 root_name=_local(root.tag)
 if root_name not in {"urlset","sitemapindex"}:raise SitemapParseError("unsupported_sitemap_root")
 kind=SitemapKind.URLSET if root_name=="urlset" else SitemapKind.SITEMAP_INDEX
 children=[item for item in root if _local(item.tag) in ({"url"} if kind is SitemapKind.URLSET else {"sitemap"})]
 maximum=limits.max_urls if kind is SitemapKind.URLSET else limits.max_sub_sitemaps
 selected=children[:maximum];limit_reached=len(children)>maximum
 seen=set();duplicates=0;candidates=[];reasons=Counter()
 for child in selected:
  raw=_text(child,"loc") or "";lastmod=_text(child,"lastmod");changefreq=_text(child,"changefreq")
  policy=validate_candidate_url(raw)
  reason=policy.reason
  if raw in seen:duplicates+=1;reason="duplicate_url"
  seen.add(raw)
  if not raw:reason="missing_loc"
  if reason:reasons[reason]+=1
  decision=FilterDecision.REJECTED if reason else FilterDecision.ACCEPTED
  normalized=policy.normalized_url if not reason else None
  fingerprint=fingerprint_metadata((raw,normalized or "",lastmod or "",changefreq or "",kind.value))
  candidates.append(SitemapCandidate(raw,normalized,policy.domain,policy.path,"url" if kind is SitemapKind.URLSET else "sitemap",lastmod,_normalize_date(lastmod),changefreq,_family_hint(policy.path),policy.scope,policy.aract_id,discovered_at,collected_at,sitemap_url,state.etag,state.last_modified,"valid" if decision is FilterDecision.ACCEPTED else "rejected",decision,reason,fingerprint))
 return kind,tuple(candidates),{"xml_entries":len(children),"duplicates":duplicates,"limit_reached":limit_reached,"rejected":sum(reasons.values()),"reasons":tuple(sorted(reasons.items()))}
