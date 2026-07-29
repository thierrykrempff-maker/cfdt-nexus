"""Deterministic extraction of source details already available to Nexus.

The module never searches a corpus and never calls a connector.  It receives
the sources already retrieved by the Runtime, qualifies them against the
factual core, and distinguishes a document that was found from one that is
absent, incomplete or version-uncertain.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Any
import unicodedata

from SYNDICAL_REASONING_ENGINE import (
    ApplicableSource,
    ApplicabilityStatus,
    CaseFactualCore,
    LegalNature,
    qualify_sources_for_extraction,
)


class DocumentAvailability(str, Enum):
    FOUND = "FOUND"
    FOUND_VERSION_UNCERTAIN = "FOUND_VERSION_UNCERTAIN"
    TITLE_ONLY = "TITLE_ONLY"
    ABSENT = "ABSENT"
    CONNECTOR_UNAVAILABLE = "CONNECTOR_UNAVAILABLE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


@dataclass(frozen=True, slots=True)
class ExtractedSource:
    source_id: str
    provider: str
    title: str
    document_type: str
    legal_nature: str
    publication_date: str | None
    effective_date: str | None
    version_date: str | None
    article_or_clause: str | None
    excerpt: str
    location: str | None
    link_to_facts: str
    availability_status: str
    applicability_status: str
    confidence: str
    hierarchy_level: int
    normative_role: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DocumentResolution:
    requested_document: str
    availability_status: DocumentAvailability
    matched_source_ids: tuple[str, ...]
    message: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["availability_status"] = self.availability_status.value
        payload["matched_source_ids"] = list(self.matched_source_ids)
        return payload


@dataclass(frozen=True, slots=True)
class SourceExtractionReport:
    sources: tuple[ExtractedSource, ...]
    document_resolutions: tuple[DocumentResolution, ...]
    rejected_sources: tuple[tuple[str, str], ...]
    retrieved_count: int
    clause_count: int
    legal_text_count: int
    documents_no_longer_to_request: int

    def to_dict(self) -> dict[str, object]:
        return {
            "sources": [item.to_dict() for item in self.sources],
            "document_resolutions": [
                item.to_dict() for item in self.document_resolutions
            ],
            "rejected_sources": [
                {"title": title, "reason": reason}
                for title, reason in self.rejected_sources
            ],
            "retrieved_count": self.retrieved_count,
            "clause_count": self.clause_count,
            "legal_text_count": self.legal_text_count,
            "documents_no_longer_to_request": self.documents_no_longer_to_request,
        }


_SOURCE_DOCUMENT_MARKERS = frozenset(
    {
        "accord",
        "avenant",
        "ccnic",
        "convention",
        "code",
        "article",
        "reglement",
        "regle",
        "procedure",
        "instruction",
        "consigne",
        "notice",
        "registre",
        "information",
        "consultation",
        "protocole",
        "decision",
        "pv",
        "cse",
        "cssct",
        "texte",
    }
)
_GENERIC = _SOURCE_DOCUMENT_MARKERS | {
    "applicable",
    "interne",
    "ineos",
    "document",
    "support",
    "exact",
    "version",
}
_SENSITIVE = re.compile(
    r"(?:[A-Z]:\\|/(?:tmp|home|Users)/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b|"
    r"\bFR\d{2}[A-Z0-9]{23}\b|\b\d{13,15}\b)",
    re.IGNORECASE,
)


def _normalize(value: object) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(
        re.findall(
            r"[a-z0-9]+",
            "".join(
                character
                for character in decomposed
                if not unicodedata.combining(character)
            ).casefold(),
        )
    )


def _tokens(value: object) -> set[str]:
    return {
        token
        for token in _normalize(value).split()
        if len(token) >= 3 and token not in {"les", "des", "une", "aux", "sur"}
    }


def _requested_text(item: object) -> str:
    if isinstance(item, Mapping):
        return " ".join(str(item.get("document") or "").split())
    return " ".join(str(item or "").split())


def _foreign_establishment(source: Mapping[str, object]) -> bool:
    establishment = _normalize(
        source.get("establishment")
        or source.get("etablissement")
        or source.get("company")
        or source.get("entreprise")
        or source.get("site")
    )
    return bool(
        establishment
        and not (
            "ineos" in establishment
            and ("sarralbe" in establishment or establishment == "ineos")
        )
    )


def _source_context(source: ApplicableSource) -> str:
    return " ".join(
        (
            source.source_provider,
            source.source_title,
            source.document_type,
            source.legal_nature.value,
            source.article_or_clause or "",
            source.precise_excerpt,
        )
    )


def _is_source_document_request(requested: str) -> bool:
    return bool(_tokens(requested) & _SOURCE_DOCUMENT_MARKERS)


def _nature_matches(requested_tokens: set[str], source: ApplicableSource) -> bool:
    nature = source.legal_nature
    if requested_tokens & {"accord", "avenant", "protocole"}:
        return nature is LegalNature.COMPANY_AGREEMENT
    if requested_tokens & {"ccnic", "convention"}:
        return nature is LegalNature.COLLECTIVE_AGREEMENT
    if requested_tokens & {"code", "article"}:
        return nature in {LegalNature.STATUTE, LegalNature.REGULATION}
    if requested_tokens & {"reglement", "regle", "procedure", "instruction", "consigne"}:
        return nature in {
            LegalNature.INTERNAL_POLICY,
            LegalNature.COMPANY_AGREEMENT,
        }
    if requested_tokens & {"pv"}:
        return nature is LegalNature.CSE_MINUTES
    return True


def _matches_request(requested: str, source: ApplicableSource) -> bool:
    requested_tokens = _tokens(requested)
    if not requested_tokens or not _nature_matches(requested_tokens, source):
        return False
    source_tokens = _tokens(_source_context(source))
    subject_tokens = requested_tokens - _GENERIC
    concept_groups = (
        {"horaire", "horaires", "poste", "postes", "3x8", "5x8", "cycle"},
        {"epi", "equipement", "protection", "visiere", "gants"},
        {"conge", "conges", "dixieme", "10"},
        {"badge", "badgeage", "tourniquet", "controle"},
        {"cssct", "cse", "delegation", "reunion"},
    )
    if any(
        requested_tokens & group and source_tokens & group
        for group in concept_groups
    ):
        return True
    if subject_tokens:
        return bool(subject_tokens & source_tokens)
    return len(requested_tokens & source_tokens) >= 2


def _normative_role(source: ApplicableSource) -> str:
    if source.legal_nature is LegalNature.CSE_MINUTES:
        return "CONTEXT_OR_EVIDENCE_ONLY"
    if source.legal_nature in {
        LegalNature.OFFICIAL_GUIDANCE,
        LegalNature.PREVENTION_GUIDANCE,
    }:
        return "GUIDANCE_NOT_AUTOMATICALLY_BINDING"
    if source.legal_nature is LegalNature.CASE_LAW:
        return "COMPARATIVE_SCOPE_DEPENDS_ON_FACTS"
    return "LEGAL_SCOPE_DEPENDS_ON_DOCUMENT_AND_APPLICABILITY"


def _version_uncertain(source: ApplicableSource) -> bool:
    return (
        source.applicability_status is ApplicabilityStatus.POTENTIALLY_APPLICABLE
        or not any(
            (
                source.effective_date,
                source.version_date,
                source.publication_date,
            )
        )
    )


def _extracted(source: ApplicableSource) -> ExtractedSource:
    status = (
        DocumentAvailability.FOUND_VERSION_UNCERTAIN.value
        if _version_uncertain(source)
        else DocumentAvailability.FOUND.value
    )
    link = source.employee_argument
    return ExtractedSource(
        source.source_id,
        source.source_provider,
        source.source_title,
        source.document_type,
        source.legal_nature.value,
        source.publication_date,
        source.effective_date,
        source.version_date,
        source.article_or_clause,
        source.precise_excerpt,
        source.source_location,
        link,
        status,
        source.applicability_status.value,
        source.confidence_level,
        source.hierarchy_level,
        _normative_role(source),
    )


def _public_safe_source(source: ApplicableSource) -> bool:
    return not _SENSITIVE.search(
        " ".join(
            (
                source.source_title,
                source.precise_excerpt,
                source.source_location or "",
            )
        )
    )


def _resolution_message(
    requested: str,
    status: DocumentAvailability,
    matches: Sequence[ApplicableSource],
) -> str:
    if status is DocumentAvailability.FOUND:
        source = matches[0]
        reference = source.article_or_clause or source.source_location or "passage identifié"
        return (
            f"L’accord ou le texte a été retrouvé : « {source.source_title} », "
            f"{reference}."
        )
    if status is DocumentAvailability.FOUND_VERSION_UNCERTAIN:
        return (
            "Le document est présent, mais sa version applicable à la date des "
            "faits reste à confirmer."
        )
    if status is DocumentAvailability.NEEDS_CLARIFICATION:
        return (
            "Le document ne peut pas être identifié précisément avant clarification "
            "du sens de la demande."
        )
    if status is DocumentAvailability.TITLE_ONLY:
        return (
            "Un document portant ce titre existe, mais aucune clause suffisamment "
            "précise n’a été retrouvée."
        )
    if status is DocumentAvailability.CONNECTOR_UNAVAILABLE:
        return "Le connecteur nécessaire est temporairement indisponible."
    return f"Le document « {requested} » n’est pas présent dans les sources retrouvées."


def build_source_extraction_report(
    core: CaseFactualCore,
    sources: Sequence[Mapping[str, object]],
    requested_documents: Sequence[object],
    *,
    unavailable_connectors: Sequence[str] = (),
) -> SourceExtractionReport:
    """Build a bounded, source-backed extraction and document resolution."""

    eligible = tuple(source for source in sources if not _foreign_establishment(source))
    foreign_rejections = tuple(
        (
            str(source.get("document") or source.get("title") or "Source"),
            "source d’un autre établissement écartée",
        )
        for source in sources
        if _foreign_establishment(source)
    )
    accepted, rejected = qualify_sources_for_extraction(core, eligible)
    citation_rows: list[ApplicableSource] = []
    seen_source_ids: set[str] = set()
    for item in accepted:
        if (
            not item.citation_ready
            or not _public_safe_source(item)
            or item.source_id in seen_source_ids
        ):
            continue
        seen_source_ids.add(item.source_id)
        citation_rows.append(item)
    citation_ready = tuple(citation_rows)
    privacy_rejections = tuple(
        (
            item.source_title,
            "source écartée de la restitution publique par le contrôle de confidentialité",
        )
        for item in accepted
        if item.citation_ready and not _public_safe_source(item)
    )
    extracted = tuple(_extracted(item) for item in citation_ready[:16])
    resolutions: list[DocumentResolution] = []
    unavailable = tuple(str(item) for item in unavailable_connectors if item)
    for raw_document in requested_documents:
        requested = _requested_text(raw_document)
        if not requested or not _is_source_document_request(requested):
            continue
        matches = tuple(
            source for source in citation_ready if _matches_request(requested, source)
        )
        if matches:
            status = (
                DocumentAvailability.FOUND_VERSION_UNCERTAIN
                if any(_version_uncertain(item) for item in matches)
                else DocumentAvailability.FOUND
            )
        elif core.blocking_ambiguities and _tokens(requested) & {"texte", "regle"}:
            status = DocumentAvailability.NEEDS_CLARIFICATION
        elif unavailable:
            status = DocumentAvailability.CONNECTOR_UNAVAILABLE
        else:
            status = DocumentAvailability.ABSENT
        resolutions.append(
            DocumentResolution(
                requested,
                status,
                tuple(item.source_id for item in matches[:3]),
                _resolution_message(requested, status, matches),
            )
        )
    found_statuses = {
        DocumentAvailability.FOUND,
        DocumentAvailability.FOUND_VERSION_UNCERTAIN,
    }
    return SourceExtractionReport(
        extracted,
        tuple(resolutions),
        (*foreign_rejections, *privacy_rejections, *rejected)[:16],
        len(extracted),
        sum(bool(item.article_or_clause and item.excerpt) for item in extracted),
        sum(
            item.legal_nature in {LegalNature.STATUTE.value, LegalNature.REGULATION.value}
            for item in extracted
        ),
        sum(item.availability_status in found_statuses for item in resolutions),
    )


def merge_metadata_source_qualifications(
    report: Mapping[str, Any] | None,
    qualifications: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    """Append metadata-only official sources without fabricating an excerpt."""

    merged = dict(report or {})
    sources = [dict(item) for item in merged.get("sources", ()) if isinstance(item, Mapping)]
    identities = {
        (_normalize(item.get("provider")), _normalize(item.get("title")))
        for item in sources
    }
    added: list[dict[str, Any]] = []
    for item in qualifications:
        provider = str(item.get("organisme") or "")
        title = str(item.get("titre") or "")
        identity = (_normalize(provider), _normalize(title))
        if not any(identity) or identity in identities:
            continue
        projected = {
                "source_id": "",
                "provider": provider,
                "title": title,
                "document_type": str(item.get("nature_document") or ""),
                "legal_nature": "OFFICIAL_METADATA",
                "publication_date": None,
                "effective_date": None,
                "version_date": None,
                "article_or_clause": None,
                "excerpt": "",
                "location": None,
                "link_to_facts": str(item.get("lien_avec_faits") or ""),
                "availability_status": DocumentAvailability.TITLE_ONLY.value,
                "applicability_status": str(item.get("portee_indicative") or ""),
                "confidence": "LOW",
                "hierarchy_level": 5,
                "normative_role": "METADATA_ONLY_NO_CLAUSE_EXTRACTED",
            }
        sources.append(projected)
        added.append(projected)
        identities.add(identity)
    merged["sources"] = sources
    merged["retrieved_count"] = len(sources)
    resolutions = [
        dict(item)
        for item in merged.get("document_resolutions", ())
        if isinstance(item, Mapping)
    ]
    for resolution in resolutions:
        if resolution.get("availability_status") != DocumentAvailability.ABSENT.value:
            continue
        requested = str(resolution.get("requested_document") or "")
        requested_tokens = _tokens(requested) - _GENERIC
        match = next(
            (
                item
                for item in added
                if requested_tokens
                and requested_tokens
                & _tokens(
                    " ".join(
                        (
                            str(item.get("title") or ""),
                            str(item.get("link_to_facts") or ""),
                        )
                    )
                )
            ),
            None,
        )
        if match:
            resolution["availability_status"] = DocumentAvailability.TITLE_ONLY.value
            resolution["message"] = _resolution_message(
                requested,
                DocumentAvailability.TITLE_ONLY,
                (),
            )
    if resolutions:
        merged["document_resolutions"] = resolutions
    return merged
