import inspect
import unittest
from datetime import datetime, timezone

from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId

from .anact_classification_models import HumanValidationStatus
from .anact_contract import AnactConnector
from .anact_page_metadata_models import PageMetadataLimits, PageMetadataStatus, PageMetadataTarget
from .anact_page_metadata_transport import AnactPageMetadataTransport, PageMetadataTransportConfig
from .anact_review_queue import AnactReviewQueue
from .anact_sitemap_transport import AnactTransportError, TransportErrorCode
from .anact_transport_models import ConditionalState, HttpResponse
from .anact_url_classifier import AnactUrlClassifier


NOW = datetime(2026, 7, 18, tzinfo=timezone.utc)
HTML = '''<!doctype html><html lang="fr"><head>
<title>Guide QVCT</title><meta name="description" content="Description officielle.">
<link rel="canonical" href="/guides/qvct">
<meta property="og:title" content="Guide QVCT"><meta property="og:type" content="article">
<meta property="article:published_time" content="2026-07-01">
<meta property="article:modified_time" content="2026-07-17">
<script type="application/ld+json">{"@type":"Article","headline":"Guide QVCT","description":"Description structurée.","url":"https://www.anact.fr/guides/qvct","datePublished":"2026-07-01","dateModified":"2026-07-17","articleBody":"CORPS INTERDIT"}</script>
</head><body><article>Texte intégral à ne jamais conserver.</article></body></html>'''.encode("utf-8")


class FakeAdapter:
    def __init__(self, response: HttpResponse):
        self.response = response
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        return self.response


def response(status=200, body=HTML, mime="text/html; charset=utf-8", url="https://www.anact.fr/guides/qvct", extra=()):
    return HttpResponse(status, url, (("Content-Type", mime),) + tuple(extra), body)


def target(url="https://www.anact.fr/guides/qvct"):
    classification = AnactUrlClassifier().classify_url(url)
    return PageMetadataTarget.from_classification(classification)


def transport(http_response=None, enabled=True, limits=PageMetadataLimits()):
    adapter = FakeAdapter(http_response or response())
    return AnactPageMetadataTransport(adapter, PageMetadataTransportConfig(enabled, limits), lambda: NOW), adapter


class AnactPageMetadataTests(unittest.TestCase):
    def test_extracts_core_metadata(self):
        result = transport()[0].inspect(target())
        value = result.metadata
        self.assertEqual(("Guide QVCT", "Description officielle.", "fr"), (value.title, value.description, value.language))
        self.assertEqual(("2026-07-01", "2026-07-17", "article"), (value.published_at, value.updated_at, value.content_type))

    def test_extracts_canonical(self): self.assertEqual("https://www.anact.fr/guides/qvct", transport()[0].inspect(target()).metadata.canonical_url)

    def test_extracts_open_graph(self):
        values = dict(transport()[0].inspect(target()).metadata.open_graph)
        self.assertEqual(("Guide QVCT", "article"), (values["og:title"], values["og:type"]))

    def test_extracts_safe_json_ld(self):
        value = transport()[0].inspect(target()).metadata.json_ld[0]
        self.assertEqual(("Article", "Guide QVCT", "2026-07-01"), (value.schema_type, value.name, value.date_published))
        self.assertFalse(hasattr(value, "article_body"))

    def test_extracts_json_ld_graph(self):
        body = b'<html><head><script type="application/ld+json">{"@graph":[{"@type":"Article","name":"X"}]}</script></head></html>'
        value = transport(response(body=body))[0].inspect(target()).metadata.json_ld
        self.assertEqual(("Article", "X"), (value[0].schema_type, value[0].name))

    def test_body_is_never_returned(self):
        value = transport()[0].inspect(target()).metadata
        self.assertIsNone(value.fulltext)
        self.assertNotIn("Texte intégral", repr(value))
        self.assertNotIn("CORPS INTERDIT", repr(value))

    def test_etag_last_modified_mime_and_length(self):
        result = transport(response(extra=(("ETag", '"abc"'), ("Last-Modified", "Thu, 17 Jul 2026 12:00:00 GMT"))))[0].inspect(target())
        value = result.metadata
        self.assertEqual(('"abc"', "Thu, 17 Jul 2026 12:00:00 GMT", "text/html", len(HTML)), (value.etag, value.last_modified, value.mime_type, value.response_length))

    def test_absent_metadata_remains_none(self):
        empty = "<html><head></head><body>Corps ignoré</body></html>".encode("utf-8")
        value = transport(response(body=empty))[0].inspect(target()).metadata
        self.assertEqual((None, None, None, None, None, None), (value.title, value.description, value.language, value.published_at, value.updated_at, value.content_type))

    def test_url_without_title_is_supported(self):
        value = transport(response(body=b'<html lang="fr"><head><meta name="description" content="x"></head></html>'))[0].inspect(target()).metadata
        self.assertIsNone(value.title)
        self.assertEqual("x", value.description)

    def test_invalid_html_is_rejected(self):
        with self.assertRaisesRegex(AnactTransportError, "invalid_html") as raised:
            transport(response(body=b"<title>broken"))[0].inspect(target())
        self.assertIs(TransportErrorCode.HTML, raised.exception.code)

    def test_invalid_json_ld_is_ignored_with_warning(self):
        body = b'<html><head><script type="application/ld+json">{bad}</script></head></html>'
        result = transport(response(body=body))[0].inspect(target())
        self.assertIn("invalid_json_ld", result.diagnostics.warnings)
        self.assertFalse(result.metadata.json_ld)

    def test_external_canonical_is_ignored(self):
        body = b'<html><head><link rel="canonical" href="https://example.invalid/x"></head></html>'
        result = transport(response(body=body))[0].inspect(target())
        self.assertIsNone(result.metadata.canonical_url)
        self.assertIn("canonical_url_rejected", result.diagnostics.warnings)

    def test_wrong_mime_is_rejected(self):
        with self.assertRaises(AnactTransportError) as raised: transport(response(mime="application/pdf"))[0].inspect(target())
        self.assertIs(TransportErrorCode.MIME, raised.exception.code)

    def test_404(self): self.assertIs(PageMetadataStatus.INVALID, transport(response(404, b""))[0].inspect(target()).status)
    def test_403(self): self.assertIs(PageMetadataStatus.ACCESS_DENIED, transport(response(403, b""))[0].inspect(target()).status)
    def test_429(self): self.assertIs(PageMetadataStatus.TEMPORARILY_UNAVAILABLE, transport(response(429, b""))[0].inspect(target()).status)
    def test_500(self): self.assertIs(PageMetadataStatus.TEMPORARILY_UNAVAILABLE, transport(response(500, b""))[0].inspect(target()).status)
    def test_304(self): self.assertIs(PageMetadataStatus.NOT_MODIFIED, transport(response(304, b""))[0].inspect(target()).status)

    def test_unresolved_redirect(self):
        with self.assertRaises(AnactTransportError) as raised: transport(response(302, b""))[0].inspect(target())
        self.assertIs(TransportErrorCode.REDIRECT, raised.exception.code)

    def test_external_redirect_is_rejected(self):
        with self.assertRaises(AnactTransportError) as raised: transport(response(url="https://example.invalid/x"))[0].inspect(target())
        self.assertIs(TransportErrorCode.REDIRECT, raised.exception.code)

    def test_internal_redirect_final_url_is_kept(self):
        result = transport(response(url="https://www.anact.fr/guides/qvct-v2"))[0].inspect(target())
        self.assertEqual("https://www.anact.fr/guides/qvct-v2", result.metadata.final_url)

    def test_disabled_by_default(self):
        value, _ = transport(enabled=False)
        with self.assertRaisesRegex(AnactTransportError, "transport_disabled"): value.inspect(target())

    def test_only_validated_classification_is_accepted(self):
        classification = AnactUrlClassifier().classify_url("https://www.anact.fr/ressource/guide-qvct")
        with self.assertRaisesRegex(ValueError, "human_validation_required"): PageMetadataTarget.from_classification(classification)
        value = PageMetadataTarget.from_classification(classification, human_status=HumanValidationStatus.ACCEPTED)
        self.assertEqual(classification.normalized_url, value.url)

    def test_accepted_review_item_is_a_valid_target(self):
        classification = AnactUrlClassifier().classify_url("https://www.anact.fr/ressource/guide-qvct")
        queue = AnactReviewQueue(); queue.add(classification)
        item = queue.accept(classification.fingerprint, "validation humaine explicite")
        self.assertEqual(classification.normalized_url, PageMetadataTarget.from_review_item(item).url)

    def test_rejected_classification_stays_rejected(self):
        classification = AnactUrlClassifier().classify_url("https://example.invalid/x")
        with self.assertRaisesRegex(ValueError, "rejected_classification"):
            PageMetadataTarget.from_classification(classification, human_status=HumanValidationStatus.ACCEPTED)

    def test_pdf_target_is_rejected_before_network(self):
        classification = AnactUrlClassifier().classify_url("https://www.anact.fr/guides/x.pdf")
        with self.assertRaises(ValueError): PageMetadataTarget.from_classification(classification)

    def test_request_is_bounded_and_has_no_credentials(self):
        value, _ = transport()
        request = value.build_request(target())
        headers = dict(request.headers)
        self.assertGreater(request.timeout_seconds, 0)
        self.assertGreater(request.max_response_bytes, 0)
        self.assertNotIn("Cookie", headers)
        self.assertNotIn("Authorization", headers)

    def test_conditional_headers(self):
        value, _ = transport()
        headers = dict(value.build_request(target(), ConditionalState('"abc"', "Thu, 17 Jul 2026 12:00:00 GMT")).headers)
        self.assertEqual('"abc"', headers["If-None-Match"])
        self.assertIn("GMT", headers["If-Modified-Since"])

    def test_size_limit(self):
        value, _ = transport(response(body=b"x" * 11), limits=PageMetadataLimits(max_response_bytes=10))
        with self.assertRaises(AnactTransportError) as raised: value.inspect(target())
        self.assertIs(TransportErrorCode.SIZE, raised.exception.code)

    def test_unknown_charset_falls_back_safely(self):
        value = transport(response(mime="text/html; charset=unknown-charset"))[0].inspect(target()).metadata
        self.assertEqual("Guide QVCT", value.title)

    def test_offline_fixture_uses_injected_adapter(self):
        value, adapter = transport()
        value.inspect(target())
        self.assertEqual(1, len(adapter.requests))

    def test_no_automatic_traversal(self):
        _, adapter = transport()
        AnactPageMetadataTransport(adapter, PageMetadataTransportConfig(enabled=True), lambda: NOW).inspect(target())
        self.assertEqual(1, len(adapter.requests))

    def test_contract_exposes_transport_without_activation(self):
        connector = AnactConnector()
        self.assertTrue(connector.page_metadata_transport_implemented)
        self.assertFalse(connector.page_metadata_transport_enabled_by_default)
        self.assertFalse(connector.enabled)
        self.assertIs(DocumentPolicy.METADATA_ONLY, connector.platform_contract.document_policy)
        self.assertIs(LicenseId.DOCUMENT_SPECIFIC, connector.platform_contract.license_id)

    def test_parser_has_no_network_or_persistence(self):
        from . import anact_page_metadata_parser as parser_module
        source = inspect.getsource(parser_module)
        for primitive in ("urlopen", "requests", "httpx", "open(", "write_text", "write_bytes"):
            self.assertNotIn(primitive, source)


if __name__ == "__main__":
    unittest.main()
