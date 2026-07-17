"""Offline HTML parser that retains only explicitly exposed page metadata."""
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from urllib.parse import urljoin

from .anact_page_metadata_models import JsonLdMetadata, PageMetadataLimits
from .anact_robots_policy import validate_candidate_url


class PageMetadataParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedPageMetadata:
    canonical_url: str | None
    title: str | None
    description: str | None
    language: str | None
    published_at: str | None
    updated_at: str | None
    content_type: str | None
    open_graph: tuple[tuple[str, str], ...]
    json_ld: tuple[JsonLdMetadata, ...]
    warnings: tuple[str, ...]


_OPEN_GRAPH_KEYS = frozenset({
    "og:title",
    "og:description",
    "og:url",
    "og:type",
    "og:locale",
    "article:published_time",
    "article:modified_time",
})
_PUBLISHED_KEYS = frozenset({"article:published_time", "datepublished", "date_published"})
_UPDATED_KEYS = frozenset({"article:modified_time", "datemodified", "date_modified", "last-modified"})


def _clean(value: object, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    return normalized if normalized and len(normalized) <= limit else None


class _MetadataParser(HTMLParser):
    def __init__(self, limits: PageMetadataLimits) -> None:
        super().__init__(convert_charrefs=True)
        self.limits = limits
        self.saw_html = False
        self.language: str | None = None
        self.title_parts: list[str] = []
        self.in_title = False
        self.title_unclosed = False
        self.description: str | None = None
        self.canonical_href: str | None = None
        self.open_graph: dict[str, str] = {}
        self.published_at: str | None = None
        self.updated_at: str | None = None
        self.json_ld_buffers: list[list[str]] = []
        self.active_json_ld: list[str] | None = None
        self.warnings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in attrs if value is not None}
        lowered = tag.lower()
        if lowered == "html":
            self.saw_html = True
            self.language = _clean(values.get("lang"), 50)
        elif lowered == "title":
            self.in_title = True
            self.title_unclosed = True
        elif lowered == "link" and "canonical" in (values.get("rel") or "").lower().split():
            self.canonical_href = _clean(values.get("href"), 2_000)
        elif lowered == "meta":
            self._meta(values)
        elif lowered == "script" and (values.get("type") or "").lower() == "application/ld+json":
            self.active_json_ld = []
            self.json_ld_buffers.append(self.active_json_ld)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
            self.title_unclosed = False
        elif tag.lower() == "script":
            self.active_json_ld = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.active_json_ld is not None:
            current_length = sum(len(part) for part in self.active_json_ld)
            if current_length + len(data) <= self.limits.max_json_ld_chars:
                self.active_json_ld.append(data)
            elif "json_ld_too_large" not in self.warnings:
                self.warnings.append("json_ld_too_large")

    def _meta(self, attrs: dict[str, str]) -> None:
        key = (attrs.get("property") or attrs.get("name") or "").strip().lower()
        content = _clean(attrs.get("content"), self.limits.max_description_chars)
        if not key or content is None:
            return
        if key == "description" and self.description is None:
            self.description = content
        if key in _OPEN_GRAPH_KEYS:
            self.open_graph.setdefault(key, content)
        if key in _PUBLISHED_KEYS and self.published_at is None:
            self.published_at = content
        if key in _UPDATED_KEYS and self.updated_at is None:
            self.updated_at = content


def _json_ld_items(buffers: list[list[str]], limits: PageMetadataLimits, warnings: list[str]) -> tuple[JsonLdMetadata, ...]:
    selected: list[JsonLdMetadata] = []
    for buffer in buffers:
        raw = "".join(buffer).strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            warnings.append("invalid_json_ld")
            continue
        values = payload if isinstance(payload, list) else [payload]
        expanded = []
        for value in values:
            if isinstance(value, dict) and isinstance(value.get("@graph"), list):
                expanded.extend(value["@graph"])
            else:
                expanded.append(value)
        values = expanded
        for value in values:
            if not isinstance(value, dict):
                continue
            selected.append(JsonLdMetadata(
                _clean(value.get("@type"), 200),
                _clean(value.get("name") or value.get("headline"), limits.max_title_chars),
                _clean(value.get("description"), limits.max_description_chars),
                _clean(value.get("url"), 2_000),
                _clean(value.get("datePublished"), 100),
                _clean(value.get("dateModified"), 100),
            ))
            if len(selected) >= limits.max_json_ld_items:
                warnings.append("json_ld_item_limit")
                return tuple(selected)
    return tuple(selected)


def parse_page_metadata(html: str, *, base_url: str, limits: PageMetadataLimits) -> ParsedPageMetadata:
    parser = _MetadataParser(limits)
    try:
        parser.feed(html)
        parser.close()
    except (ValueError, AssertionError) as error:
        raise PageMetadataParseError("invalid_html") from error
    if not parser.saw_html or parser.title_unclosed:
        raise PageMetadataParseError("invalid_html")

    warnings = list(parser.warnings)
    canonical_url = None
    if parser.canonical_href:
        candidate = urljoin(base_url, parser.canonical_href)
        policy = validate_candidate_url(candidate)
        if policy.allowed:
            canonical_url = policy.normalized_url
        else:
            warnings.append("canonical_url_rejected")

    json_ld = _json_ld_items(parser.json_ld_buffers, limits, warnings)
    title = _clean("".join(parser.title_parts), limits.max_title_chars)
    published = parser.published_at or next((item.date_published for item in json_ld if item.date_published), None)
    updated = parser.updated_at or next((item.date_modified for item in json_ld if item.date_modified), None)
    content_type = parser.open_graph.get("og:type") or next((item.schema_type for item in json_ld if item.schema_type), None)
    return ParsedPageMetadata(
        canonical_url,
        title,
        parser.description,
        parser.language,
        published,
        updated,
        content_type,
        tuple(sorted(parser.open_graph.items())),
        json_ld,
        tuple(sorted(set(warnings))),
    )
