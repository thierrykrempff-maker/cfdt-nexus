import unittest
from datetime import datetime,timezone

from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId

from .anact_contract import AnactConnector
from .anact_robots_policy import validate_candidate_url
from .anact_sitemap_parser import SitemapParseError,parse_sitemap
from .anact_sitemap_transport import AnactSitemapTransport,AnactTransportError,SitemapTransportConfig,TransportErrorCode
from .anact_transport_models import ConditionalState,FetchStatus,FilterDecision,HttpResponse,SitemapKind,TransportLimits

NOW=datetime(2026,7,17,tzinfo=timezone.utc)
VALID_XML=b'''<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.anact.fr/themes</loc><lastmod>2026-07-16T10:00Z</lastmod><changefreq>monthly</changefreq><unknown>x</unknown></url><url><loc>https://www.anact.fr/grand-est</loc></url></urlset>'''

class FakeAdapter:
 def __init__(self,response=None,error=None):self.response=response;self.error=error;self.requests=[]
 def send(self,request):self.requests.append(request);raise self.error if self.error else _Return(self.response)
class _Return(Exception):pass

class WorkingFakeAdapter(FakeAdapter):
 def send(self,request):self.requests.append(request);return self.response
class ErrorAdapter:
 def __init__(self,error):self.error=error
 def send(self,request):raise self.error

def response(status=200,body=VALID_XML,mime="text/xml; charset=utf-8",url="https://www.anact.fr/sitemap.xml",extra=()):return HttpResponse(status,url,(("Content-Type",mime),)+tuple(extra),body)
def transport(http_response=response(),limits=TransportLimits(),enabled=True):return AnactSitemapTransport(WorkingFakeAdapter(http_response),SitemapTransportConfig(enabled,limits),lambda:NOW)

class AnactSitemapTransportTests(unittest.TestCase):
 def test_disabled_by_default(self):
  with self.assertRaisesRegex(AnactTransportError,"transport_disabled"):AnactSitemapTransport(WorkingFakeAdapter(response())).inspect()
 def test_connector_stays_disabled(self):self.assertFalse(AnactConnector.enabled);self.assertEqual("architecture_only",AnactConnector.connector_status);self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_transport_status_distinction(self):self.assertTrue(AnactConnector.sitemap_transport_implemented);self.assertFalse(AnactConnector.sitemap_transport_enabled_by_default)
 def test_policy_and_license_unchanged(self):self.assertIs(DocumentPolicy.METADATA_ONLY,AnactConnector.platform_contract.document_policy);self.assertIs(LicenseId.DOCUMENT_SPECIFIC,AnactConnector.platform_contract.license_id)
 def test_https_required(self):self.assertEqual("https_required",validate_candidate_url("http://www.anact.fr/x").reason)
 def test_domain_required(self):self.assertEqual("domain_not_allowed",validate_candidate_url("https://example.invalid/x").reason)
 def test_credentials_refused(self):self.assertEqual("embedded_credentials",validate_candidate_url("https://user@www.anact.fr/x").reason)
 def test_fragment_removed(self):self.assertEqual("https://www.anact.fr/themes",validate_candidate_url("https://www.anact.fr/themes#x").normalized_url)
 def test_query_refused(self):self.assertEqual("query_parameters_not_authorized",validate_candidate_url("https://www.anact.fr/themes?x=1").reason)
 def test_faceted_pagination_refused(self):self.assertEqual("faceted_pagination_forbidden",validate_candidate_url("https://www.anact.fr/actualites?page=2").reason)
 def test_search_refused(self):self.assertEqual("robots_forbidden_path",validate_candidate_url("https://www.anact.fr/search/x").reason)
 def test_pdf_refused(self):self.assertEqual("downloadable_document_forbidden",validate_candidate_url("https://www.anact.fr/x.pdf").reason)
 def test_regional_entity_recognized(self):value=validate_candidate_url("https://www.anact.fr/grand-est");self.assertEqual(("regional","grand_est"),(value.scope,value.aract_id))
 def test_unknown_region_not_invented(self):value=validate_candidate_url("https://www.anact.fr/region-inconnue");self.assertEqual(("national",None),(value.scope,value.aract_id))
 def test_request_security_headers(self):
  value=transport();request=value.build_request();headers=dict(request.headers);self.assertIn("User-Agent",headers);self.assertIn("Accept",headers);self.assertNotIn("Cookie",headers);self.assertNotIn("Authorization",headers);self.assertGreater(request.timeout_seconds,0)
 def test_conditional_headers(self):
  request=transport().build_request(ConditionalState('"abc"',"Thu, 16 Jul 2026 23:01:45 GMT"));headers=dict(request.headers);self.assertEqual('"abc"',headers["If-None-Match"]);self.assertIn("GMT",headers["If-Modified-Since"])
 def test_200_urlset(self):value=transport().inspect();self.assertIs(FetchStatus.FETCHED,value.status);self.assertIs(SitemapKind.URLSET,value.kind);self.assertEqual(2,len(value.candidates));self.assertEqual(2,value.diagnostics.valid_entries)
 def test_etag_last_modified_preserved(self):value=transport(response(extra=(("ETag",'"abc"'),("Last-Modified","Thu, 16 Jul 2026 23:01:45 GMT")))).inspect();self.assertEqual('"abc"',value.conditional_state.etag);self.assertIn("GMT",value.conditional_state.last_modified)
 def test_304(self):value=transport(response(304,b"",mime="text/xml")).inspect(ConditionalState('"abc"'));self.assertIs(FetchStatus.NOT_MODIFIED,value.status);self.assertFalse(value.candidates)
 def test_403(self):self.assertIs(FetchStatus.ACCESS_DENIED,transport(response(403,b"")).inspect().status)
 def test_404(self):self.assertIs(FetchStatus.INVALID,transport(response(404,b"")).inspect().status)
 def test_429(self):self.assertIs(FetchStatus.TEMPORARILY_UNAVAILABLE,transport(response(429,b"")).inspect().status)
 def test_500(self):self.assertIs(FetchStatus.TEMPORARILY_UNAVAILABLE,transport(response(500,b"")).inspect().status)
 def test_unresolved_redirect(self):
  with self.assertRaises(AnactTransportError) as raised:transport(response(302,b"")).inspect()
  self.assertIs(TransportErrorCode.REDIRECT,raised.exception.code)
 def test_external_redirect_refused(self):
  with self.assertRaises(AnactTransportError) as raised:transport(response(url="https://example.invalid/sitemap.xml")).inspect()
  self.assertIs(TransportErrorCode.REDIRECT,raised.exception.code)
 def test_timeout_structured(self):
  with self.assertRaises(AnactTransportError) as raised:AnactSitemapTransport(ErrorAdapter(AnactTransportError(TransportErrorCode.TIMEOUT,"network_timeout")),SitemapTransportConfig(enabled=True)).inspect()
  self.assertIs(TransportErrorCode.TIMEOUT,raised.exception.code)
 def test_tls_structured(self):
  with self.assertRaises(AnactTransportError) as raised:AnactSitemapTransport(ErrorAdapter(AnactTransportError(TransportErrorCode.TLS,"tls_error")),SitemapTransportConfig(enabled=True)).inspect()
  self.assertIs(TransportErrorCode.TLS,raised.exception.code)
 def test_network_error_structured(self):
  with self.assertRaises(AnactTransportError) as raised:AnactSitemapTransport(ErrorAdapter(AnactTransportError(TransportErrorCode.NETWORK,"network_error")),SitemapTransportConfig(enabled=True)).inspect()
  self.assertIs(TransportErrorCode.NETWORK,raised.exception.code)
 def test_invalid_mime(self):
  with self.assertRaises(AnactTransportError) as raised:transport(response(mime="text/html")).inspect()
  self.assertIs(TransportErrorCode.MIME,raised.exception.code)
 def test_size_limit(self):
  with self.assertRaises(AnactTransportError) as raised:transport(response(body=b"x"*11),TransportLimits(max_response_bytes=10)).inspect()
  self.assertIs(TransportErrorCode.SIZE,raised.exception.code)
 def test_malformed_xml(self):
  with self.assertRaises(AnactTransportError) as raised:transport(response(body=b"<urlset>")).inspect()
  self.assertIs(TransportErrorCode.XML,raised.exception.code)
 def test_unsafe_xml(self):
  with self.assertRaises(SitemapParseError):parse_sitemap(b'<!DOCTYPE x [<!ENTITY y "z">]><urlset/>',sitemap_url="https://www.anact.fr/sitemap.xml",state=ConditionalState(),limits=TransportLimits(),discovered_at=NOW,collected_at=NOW)
 def test_sitemap_index(self):
  xml=b'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://www.anact.fr/sub-sitemap.xml</loc></sitemap></sitemapindex>';kind,candidates,_=parse_sitemap(xml,sitemap_url="https://www.anact.fr/sitemap.xml",state=ConditionalState(),limits=TransportLimits(),discovered_at=NOW,collected_at=NOW);self.assertIs(SitemapKind.SITEMAP_INDEX,kind);self.assertEqual("sitemap",candidates[0].entry_type)
 def test_missing_lastmod(self):value=transport().inspect();self.assertIsNone(value.candidates[1].lastmod_raw);self.assertIsNone(value.candidates[1].lastmod_normalized)
 def test_invalid_date(self):
  xml=b'<urlset><url><loc>https://www.anact.fr/x</loc><lastmod>invalid</lastmod></url></urlset>';_,candidates,_=parse_sitemap(xml,sitemap_url="https://www.anact.fr/sitemap.xml",state=ConditionalState(),limits=TransportLimits(),discovered_at=NOW,collected_at=NOW);self.assertIsNone(candidates[0].lastmod_normalized)
 def test_duplicates(self):
  xml=b'<urlset><url><loc>https://www.anact.fr/x</loc></url><url><loc>https://www.anact.fr/x</loc></url></urlset>';_,candidates,counts=parse_sitemap(xml,sitemap_url="https://www.anact.fr/sitemap.xml",state=ConditionalState(),limits=TransportLimits(),discovered_at=NOW,collected_at=NOW);self.assertEqual(1,counts["duplicates"]);self.assertIs(FilterDecision.REJECTED,candidates[1].decision)
 def test_external_url_rejected_not_hidden(self):
  xml=b'<urlset><url><loc>https://example.invalid/x</loc></url></urlset>';_,candidates,_=parse_sitemap(xml,sitemap_url="https://www.anact.fr/sitemap.xml",state=ConditionalState(),limits=TransportLimits(),discovered_at=NOW,collected_at=NOW);self.assertEqual("domain_not_allowed",candidates[0].rejection_reason)
 def test_url_limit(self):
  xml=b'<urlset><url><loc>https://www.anact.fr/a</loc></url><url><loc>https://www.anact.fr/b</loc></url></urlset>';_,candidates,counts=parse_sitemap(xml,sitemap_url="https://www.anact.fr/sitemap.xml",state=ConditionalState(),limits=TransportLimits(max_urls=1),discovered_at=NOW,collected_at=NOW);self.assertEqual(1,len(candidates));self.assertTrue(counts["limit_reached"])
 def test_no_fulltext(self):self.assertTrue(all(candidate.fulltext is None for candidate in transport().inspect().candidates))
 def test_deterministic_candidates(self):self.assertEqual(transport().inspect().candidates,transport().inspect().candidates)
 def test_general_fetch_and_sync_still_blocked(self):
  connector=AnactConnector()
  with self.assertRaises(RuntimeError):connector.fetch("x")
  with self.assertRaises(RuntimeError):connector.synchronize()

if __name__=="__main__":unittest.main()
