"""Structured local search over ANACT catalogue metadata only."""
from datetime import datetime, timezone

from .anact_document_catalog_models import CatalogDocument, CatalogQuery


def _contains(value: str | None, term: str | None) -> bool:
    return term is None or (value is not None and term.casefold() in value.casefold())


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _matches_date(document: CatalogDocument, query: CatalogQuery) -> bool:
    if query.date_from is None and query.date_to is None:
        return True
    start = _date(query.date_from)
    end = _date(query.date_to)
    if query.date_from is not None and start is None:
        raise ValueError("invalid date_from")
    if query.date_to is not None and end is None:
        raise ValueError("invalid date_to")
    dates = tuple(value for value in (_date(document.published_at), _date(document.updated_at)) if value is not None)
    return any((start is None or value >= start) and (end is None or value <= end) for value in dates)


def search_documents(documents: tuple[CatalogDocument, ...], query: CatalogQuery) -> tuple[CatalogDocument, ...]:
    selected = (
        document
        for document in documents
        if (query.category is None or document.category == query.category)
        and (query.region_id is None or document.region_id == query.region_id)
        and (query.language is None or document.language == query.language)
        and (query.lifecycle is None or document.lifecycle is query.lifecycle)
        and (query.validation_decision is None or document.validation_decision == query.validation_decision)
        and (query.human_validation_status is None or document.human_validation_status == query.human_validation_status)
        and _matches_date(document, query)
        and _contains(document.title, query.title_term)
        and _contains(document.description, query.description_term)
    )
    return tuple(sorted(selected, key=lambda item: ((item.title or "").casefold(), item.document_id)))
