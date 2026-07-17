"""Explicit one-page ANACT metadata reader; never returns or persists HTML."""
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Callable

from .anact_page_metadata_models import (
    PageMetadata,
    PageMetadataDiagnostics,
    PageMetadataLimits,
    PageMetadataResult,
    PageMetadataStatus,
    PageMetadataTarget,
)
from .anact_page_metadata_parser import PageMetadataParseError, parse_page_metadata
from .anact_robots_policy import validate_candidate_url
from .anact_sitemap_transport import AnactTransportError, HttpAdapter, TransportErrorCode
from .anact_transport_models import ConditionalState, HttpRequest, HttpResponse


PAGE_USER_AGENT = "CFDT-Nexus-ANACT-PageMetadata/1.0 (+metadata-only; contact=repository-maintainer)"
ACCEPTED_PAGE_MIME_TYPES = frozenset({"text/html", "application/xhtml+xml"})


@dataclass(frozen=True)
class PageMetadataTransportConfig:
    enabled: bool = False
    limits: PageMetadataLimits = PageMetadataLimits()


class AnactPageMetadataTransport:
    def __init__(
        self,
        adapter: HttpAdapter,
        config: PageMetadataTransportConfig = PageMetadataTransportConfig(),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.adapter = adapter
        self.config = config
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def build_request(self, target: PageMetadataTarget, state: ConditionalState = ConditionalState()) -> HttpRequest:
        policy = validate_candidate_url(target.url)
        if not policy.allowed:
            raise AnactTransportError(TransportErrorCode.DOMAIN, policy.reason or "url_not_allowed")
        headers = [
            ("Accept", "text/html, application/xhtml+xml;q=0.9"),
            ("User-Agent", PAGE_USER_AGENT),
        ]
        if state.etag:
            headers.append(("If-None-Match", state.etag))
        if state.last_modified:
            headers.append(("If-Modified-Since", state.last_modified))
        limits = self.config.limits
        return HttpRequest(target.url, tuple(headers), limits.timeout_seconds, limits.max_redirects, limits.max_response_bytes)

    def inspect(
        self,
        target: PageMetadataTarget,
        state: ConditionalState = ConditionalState(),
    ) -> PageMetadataResult:
        if not self.config.enabled:
            raise AnactTransportError(TransportErrorCode.DISABLED, "transport_disabled")
        request = self.build_request(target, state)
        response = self.adapter.send(request)
        policy = validate_candidate_url(response.url)
        if not policy.allowed:
            raise AnactTransportError(TransportErrorCode.REDIRECT, policy.reason or "redirect_not_allowed", response.status)
        mime = (response.header("Content-Type") or "").split(";", 1)[0].strip().lower() or None
        etag = response.header("ETag") or state.etag
        last_modified = response.header("Last-Modified") or state.last_modified

        if response.status == 304:
            return self._empty(PageMetadataStatus.NOT_MODIFIED, target, response, mime, etag, last_modified)
        if response.status in {401, 403}:
            return self._empty(PageMetadataStatus.ACCESS_DENIED, target, response, mime, etag, last_modified, "access_denied")
        if response.status == 404:
            return self._empty(PageMetadataStatus.INVALID, target, response, mime, etag, last_modified, "not_found")
        if response.status == 429 or 500 <= response.status <= 599:
            return self._empty(PageMetadataStatus.TEMPORARILY_UNAVAILABLE, target, response, mime, etag, last_modified, f"http_{response.status}")
        if response.status in {301, 302}:
            raise AnactTransportError(TransportErrorCode.REDIRECT, "unresolved_redirect", response.status)
        if response.status != 200:
            raise AnactTransportError(TransportErrorCode.HTTP, f"unexpected_http_{response.status}", response.status)
        if mime not in ACCEPTED_PAGE_MIME_TYPES:
            raise AnactTransportError(TransportErrorCode.MIME, "unexpected_mime_type", response.status)
        if len(response.body) > self.config.limits.max_response_bytes:
            raise AnactTransportError(TransportErrorCode.SIZE, "response_too_large", response.status)

        encoding = self._encoding(response.header("Content-Type"))
        try:
            html = response.body.decode(encoding, errors="replace")
        except LookupError:
            html = response.body.decode("utf-8", errors="replace")
        try:
            parsed = parse_page_metadata(html, base_url=response.url, limits=self.config.limits)
        except PageMetadataParseError as error:
            raise AnactTransportError(TransportErrorCode.HTML, str(error), response.status) from error
        metadata = PageMetadata(
            target.url,
            response.url,
            parsed.canonical_url,
            parsed.title,
            parsed.description,
            parsed.language,
            parsed.published_at,
            parsed.updated_at,
            parsed.content_type,
            parsed.open_graph,
            parsed.json_ld,
            etag,
            last_modified,
            mime,
            len(response.body),
            target.classification_fingerprint,
            target.category,
            target.region_id,
            self.clock(),
        )
        diagnostics = PageMetadataDiagnostics(target.url, response.url, response.status, mime, len(response.body), parsed.warnings, PageMetadataStatus.FETCHED)
        return PageMetadataResult(PageMetadataStatus.FETCHED, metadata, etag, last_modified, diagnostics)

    @staticmethod
    def _encoding(content_type: str | None) -> str:
        match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type or "", re.IGNORECASE)
        return match.group(1) if match else "utf-8"

    @staticmethod
    def _empty(status, target, response: HttpResponse, mime, etag, last_modified, error=None) -> PageMetadataResult:
        diagnostics = PageMetadataDiagnostics(target.url, response.url, response.status, mime, len(response.body), (), status, error)
        return PageMetadataResult(status, None, etag, last_modified, diagnostics)
