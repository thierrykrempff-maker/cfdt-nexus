"""Typed evidence bridge from retrieval results to legal reasoning.

The module is intentionally deterministic and side-effect free.  It does not
execute a connector.  It only validates, links, ranks and projects documents
already returned by :class:`SourceExecutionCoordinator`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import re
from typing import Mapping, Sequence

from .legal_issue_models import ResearchPlan, SourceFamily
from .retrieval_models import (
    ConnectorExecutionSummary,
    RESULT_STATUSES,
    RetrievalStatus,
    RetrievedDocument,
    redact_public_value,
)


class EvidenceSourceType(str, Enum):
    COMPANY_AGREEMENT = "COMPANY_AGREEMENT"
    COLLECTIVE_AGREEMENT = "COLLECTIVE_AGREEMENT"
    STATUTE_OR_REGULATION = "STATUTE_OR_REGULATION"
    CASE_LAW = "CASE_LAW"
    INTERNAL_POLICY = "INTERNAL_POLICY"
    INTERNAL_PRACTICE = "INTERNAL_PRACTICE"
    CSE_CSSCT_MINUTES = "CSE_CSSCT_MINUTES"
    OFFICIAL_GUIDANCE = "OFFICIAL_GUIDANCE"
    METADATA_ONLY_CATALOG = "METADATA_ONLY_CATALOG"
    LOCAL_DOCUMENT = "LOCAL_DOCUMENT"
    UNUSABLE = "UNUSABLE"


_PRIORITY = {
    EvidenceSourceType.COMPANY_AGREEMENT: 1,
    EvidenceSourceType.COLLECTIVE_AGREEMENT: 2,
    EvidenceSourceType.STATUTE_OR_REGULATION: 3,
    EvidenceSourceType.CASE_LAW: 4,
    EvidenceSourceType.INTERNAL_POLICY: 5,
    EvidenceSourceType.INTERNAL_PRACTICE: 5,
    EvidenceSourceType.LOCAL_DOCUMENT: 5,
    EvidenceSourceType.CSE_CSSCT_MINUTES: 6,
    EvidenceSourceType.OFFICIAL_GUIDANCE: 7,
    EvidenceSourceType.METADATA_ONLY_CATALOG: 8,
    EvidenceSourceType.UNUSABLE: 9,
}
_PUBLIC_RESULT_STATUSES = {
    RetrievalStatus.LOCAL_DOCUMENT,
    RetrievalStatus.LIVE_RESULT_OBTAINED,
    RetrievalStatus.CACHE_RESULT,
    RetrievalStatus.STALE_CACHE_RESULT,
}
_SPACE = re.compile(r"\s+")
_PUBLIC_HEALTH_DETAIL = re.compile(
    r"\b(?:diagnostic|maladie|traitement|hospitalis\w*|invalidit\w*|grossess\w*|"
    r"handicap\w*|gastr\w*|sang|selles?)\b",
    re.IGNORECASE,
)


def _clean(value: object, *, limit: int = 1200) -> str | None:
    text = redact_public_value(value, max_length=limit)
    if not text:
        return None
    text = _SPACE.sub(" ", text).strip()
    return text or None


def _stable(*parts: object) -> str:
    digest = hashlib.sha256(
        "\x1f".join(str(part or "") for part in parts).encode("utf-8")
    ).hexdigest()[:24]
    return f"evidence-{digest}"


def _public_excerpt(value: object) -> str | None:
    """Remove medically sensitive segments while preserving useful context."""

    text = _clean(value, limit=700)
    if not text:
        return None
    segments = re.split(r"(?<=[.!?])\s+", text)
    retained = [
        segment
        for segment in segments
        if segment and not _PUBLIC_HEALTH_DETAIL.search(segment)
    ]
    return _clean(" ".join(retained), limit=700)


def _provenance(document: RetrievedDocument) -> dict[str, str]:
    return {str(key): str(value) for key, value in document.provenance}


def _source_type(
    family: SourceFamily,
    document: RetrievedDocument,
) -> EvidenceSourceType:
    if document.status in {
        RetrievalStatus.METADATA_ONLY,
        RetrievalStatus.TITLE_ONLY,
    }:
        return EvidenceSourceType.METADATA_ONLY_CATALOG
    if document.rejected or document.status not in RESULT_STATUSES:
        return EvidenceSourceType.UNUSABLE
    return {
        SourceFamily.INEOS_AGREEMENT: EvidenceSourceType.COMPANY_AGREEMENT,
        SourceFamily.CCNIC_IDCC_44: EvidenceSourceType.COLLECTIVE_AGREEMENT,
        SourceFamily.LABOUR_CODE: EvidenceSourceType.STATUTE_OR_REGULATION,
        SourceFamily.REGULATION: EvidenceSourceType.STATUTE_OR_REGULATION,
        SourceFamily.CASE_LAW: EvidenceSourceType.CASE_LAW,
        SourceFamily.INEOS_INTERNAL_RULE: EvidenceSourceType.INTERNAL_POLICY,
        SourceFamily.INEOS_PROCEDURE: EvidenceSourceType.INTERNAL_POLICY,
        SourceFamily.INTERNAL_PRACTICE: EvidenceSourceType.INTERNAL_PRACTICE,
        SourceFamily.CSE_MINUTES: EvidenceSourceType.CSE_CSSCT_MINUTES,
        SourceFamily.CSSCT_MINUTES: EvidenceSourceType.CSE_CSSCT_MINUTES,
        SourceFamily.OFFICIAL_GUIDANCE: EvidenceSourceType.OFFICIAL_GUIDANCE,
        SourceFamily.EMPLOYMENT_CONTRACT: EvidenceSourceType.LOCAL_DOCUMENT,
        SourceFamily.OTHER: EvidenceSourceType.LOCAL_DOCUMENT,
    }[family]


def _legal_value(source_type: EvidenceSourceType, supplied: str | None) -> str:
    if source_type is EvidenceSourceType.CSE_CSSCT_MINUTES:
        return (
            "Contexte, chronologie ou élément de preuve ; ce passage ne constitue "
            "pas une norme juridique."
        )
    if source_type is EvidenceSourceType.METADATA_ONLY_CATALOG:
        return "Métadonnée de repérage uniquement ; aucun contenu documentaire obtenu."
    return supplied or {
        EvidenceSourceType.COMPANY_AGREEMENT: "Accord d'entreprise à vérifier dans son champ et sa version.",
        EvidenceSourceType.COLLECTIVE_AGREEMENT: "Convention collective à vérifier dans son champ et sa version.",
        EvidenceSourceType.STATUTE_OR_REGULATION: "Texte officiel à vérifier dans sa version applicable.",
        EvidenceSourceType.CASE_LAW: "Décision de comparaison ; sa portée dépend des faits et de la juridiction.",
        EvidenceSourceType.INTERNAL_POLICY: "Règle interne à vérifier quant à sa diffusion et son opposabilité.",
        EvidenceSourceType.INTERNAL_PRACTICE: "Pratique interne ; ne vaut pas automatiquement norme juridique.",
        EvidenceSourceType.OFFICIAL_GUIDANCE: "Ressource officielle d'information ou de méthode.",
        EvidenceSourceType.LOCAL_DOCUMENT: "Document local à qualifier selon sa nature.",
        EvidenceSourceType.UNUSABLE: "Source non exploitable.",
        EvidenceSourceType.METADATA_ONLY_CATALOG: "",
        EvidenceSourceType.CSE_CSSCT_MINUTES: "",
    }[source_type]


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    evidence_id: str
    case_session_id: str
    issue_id: str
    fact_ids: tuple[str, ...]
    missing_information_ids: tuple[str, ...]
    query_id: str
    target_id: str
    research_objective: str
    relevance_justification: str
    source_family: SourceFamily
    source_type: EvidenceSourceType
    provenance: tuple[tuple[str, str], ...]
    retrieval_status: RetrievalStatus
    document_id: str
    title: str
    reference: str | None
    date: str | None
    excerpt: str | None
    establishment_scope: str | None
    temporal_scope: str | None
    relevance_score: int
    selection_reasons: tuple[str, ...]
    limits: tuple[str, ...]
    legal_value: str
    sensitive: bool
    usable_in_public_response: bool

    def __post_init__(self) -> None:
        required = (
            self.evidence_id,
            self.case_session_id,
            self.issue_id,
            self.query_id,
            self.target_id,
            self.research_objective,
            self.relevance_justification,
            self.document_id,
            self.title,
            self.legal_value,
        )
        if not all(str(value).strip() for value in required):
            raise ValueError("evidence identity, linkage and qualification are required")
        if not self.fact_ids:
            raise ValueError("evidence must be linked to at least one canonical fact")
        if not 0 <= self.relevance_score <= 100:
            raise ValueError("evidence relevance score must be between 0 and 100")
        if self.usable_in_public_response and (
            self.sensitive
            or not self.excerpt
            or self.retrieval_status not in _PUBLIC_RESULT_STATUSES
            or self.source_type
            in {
                EvidenceSourceType.METADATA_ONLY_CATALOG,
                EvidenceSourceType.UNUSABLE,
            }
        ):
            raise ValueError("public evidence must contain a safe retrieved excerpt")

    @property
    def hierarchy_priority(self) -> int:
        return _PRIORITY[self.source_type]

    def to_dict(self, *, public: bool = False) -> dict[str, object]:
        payload = asdict(self)
        payload["source_family"] = self.source_family.value
        payload["source_type"] = self.source_type.value
        payload["retrieval_status"] = self.retrieval_status.value
        if public:
            provenance = dict(self.provenance)
            payload["organization"] = (
                provenance.get("provider") or self.source_family.value
            )
            payload["passage_nature"] = provenance.get("passage_nature")
            for key in (
                "evidence_id",
                "case_session_id",
                "issue_id",
                "fact_ids",
                "missing_information_ids",
                "query_id",
                "target_id",
                "document_id",
                "provenance",
            ):
                payload.pop(key, None)
            payload["excerpt"] = _public_excerpt(self.excerpt)
        return payload

    def to_source_record(self) -> dict[str, object]:
        """Project an accepted bundle to the pre-existing source-to-facts contract."""

        layer = {
            EvidenceSourceType.COMPANY_AGREEMENT: "accord entreprise",
            EvidenceSourceType.COLLECTIVE_AGREEMENT: "convention collective",
            EvidenceSourceType.STATUTE_OR_REGULATION: "code travail",
            EvidenceSourceType.CASE_LAW: "jurisprudence",
            EvidenceSourceType.INTERNAL_POLICY: "accord entreprise",
            EvidenceSourceType.INTERNAL_PRACTICE: "accord entreprise",
            EvidenceSourceType.CSE_CSSCT_MINUTES: "historique cse",
        }.get(self.source_type, "pratique officielle")
        return {
            "provider": dict(self.provenance).get("provider", "Source retrouvée"),
            "document": self.title,
            "document_type": self.source_type.value,
            "source_layer": layer,
            "precise_excerpt": self.excerpt,
            "article_or_section": self.reference,
            "publication_date": self.date,
            "location": self.reference,
            "retrieval_status": self.retrieval_status.value,
            "score": self.relevance_score,
            "selection_reasons": list(self.selection_reasons),
            "selection_limits": list(self.limits),
            "_context": " ".join(
                (
                    self.research_objective,
                    self.relevance_justification,
                    *self.selection_reasons,
                )
            ),
        }


@dataclass(frozen=True, slots=True)
class EvidenceSelection:
    received: tuple[EvidenceBundle, ...]
    selected: tuple[EvidenceBundle, ...]
    rejected: tuple[tuple[str, str], ...]

    def to_dict(self, *, public: bool = False) -> dict[str, object]:
        return {
            "received_count": len(self.received),
            "selected_count": len(self.selected),
            "rejected_count": len(self.rejected),
            "evidence": [item.to_dict(public=public) for item in self.selected],
            "rejected": (
                []
                if public
                else [
                    {"evidence_id": evidence_id, "reason": reason}
                    for evidence_id, reason in self.rejected
                ]
            ),
        }


def build_evidence_bundles(
    plan: ResearchPlan,
    summary: ConnectorExecutionSummary,
) -> tuple[EvidenceBundle, ...]:
    """Link retrieved documents to the exact issue, query and canonical facts."""

    if summary.case_session_id != plan.case_session_id or summary.plan_id != plan.plan_id:
        raise ValueError("retrieval summary does not belong to the research plan")
    events = {event.event_id: event for event in summary.events}
    queries = {
        query.query_id: query for query in (*plan.queries, *plan.blocked_queries)
    }
    targets = {target.target_id: target for target in plan.targets}
    issues = {issue.issue_id: issue for issue in plan.issues}
    bundles: list[EvidenceBundle] = []
    for document in summary.documents:
        event = events.get(document.event_id)
        if event is None:
            raise ValueError("retrieved document has no trace event")
        query = queries.get(event.query_id)
        target = targets.get(event.target_id)
        issue = issues.get(event.issue_id)
        if query is None or target is None or issue is None:
            raise ValueError("retrieval trace is not linked to the research plan")
        if (
            query.issue_id != issue.issue_id
            or query.target_id != target.target_id
            or event.case_session_id != issue.case_session_id
        ):
            raise ValueError("cross-issue or cross-case retrieval contamination")
        family = SourceFamily(event.source_family)
        source_type = _source_type(family, document)
        provenance = _provenance(document)
        excerpt = _clean(document.normalized_excerpt or document.raw_excerpt)
        supplied_score = provenance.get("final_score")
        try:
            relevance = round(float(supplied_score) * 100) if supplied_score else 50
        except (TypeError, ValueError):
            relevance = 50
        relevance = min(100, max(0, relevance))
        reasons = tuple(
            item
            for item in (
                _clean(provenance.get("proves"), limit=360),
                _clean(provenance.get("qualification_reason"), limit=360),
            )
            if item
        )
        limits = tuple(
            item
            for item in (
                _clean(provenance.get("does_not_prove"), limit=420),
                *(_clean(reason, limit=240) for reason in document.rejection_reasons),
            )
            if item
        )
        usable = bool(
            not document.rejected
            and not document.sensitive
            and excerpt
            and document.status in _PUBLIC_RESULT_STATUSES
            and source_type
            not in {
                EvidenceSourceType.METADATA_ONLY_CATALOG,
                EvidenceSourceType.UNUSABLE,
            }
        )
        bundles.append(
            EvidenceBundle(
                evidence_id=_stable(
                    plan.case_session_id,
                    issue.issue_id,
                    query.query_id,
                    document.document_id,
                ),
                case_session_id=plan.case_session_id,
                issue_id=issue.issue_id,
                fact_ids=issue.associated_fact_ids,
                missing_information_ids=issue.missing_information_ids,
                query_id=query.query_id,
                target_id=target.target_id,
                research_objective=target.purpose,
                relevance_justification=(
                    reasons[0]
                    if reasons
                    else "Le document a été retenu par la recherche planifiée pour cette question."
                ),
                source_family=family,
                source_type=source_type,
                provenance=tuple(
                    (key, value)
                    for key, value in (
                        ("provider", document.provider),
                        ("connector_id", event.connector_id),
                        ("connector_kind", event.connector_kind.value),
                        ("status", event.status.value),
                        ("passage_nature", provenance.get("passage_nature", "")),
                    )
                    if value
                ),
                retrieval_status=document.status,
                document_id=document.document_id,
                title=_clean(document.title, limit=260) or "Source sans titre",
                reference=_clean(
                    document.public_reference
                    or document.article_number
                    or document.clause_number
                    or document.page,
                    limit=260,
                ),
                date=_clean(document.date, limit=40),
                excerpt=excerpt,
                establishment_scope=_clean(document.establishment_scope, limit=120),
                temporal_scope=_clean(document.temporal_scope, limit=120),
                relevance_score=relevance,
                selection_reasons=reasons,
                limits=limits,
                legal_value=_legal_value(
                    source_type, _clean(provenance.get("legal_value"), limit=300)
                ),
                sensitive=document.sensitive,
                usable_in_public_response=usable,
            )
        )
    return tuple(bundles)


def select_evidence(
    bundles: Sequence[EvidenceBundle],
    *,
    max_per_issue: int = 3,
    max_minutes_per_issue: int = 2,
) -> EvidenceSelection:
    """Apply hierarchy, public-safety and deterministic deduplication rules."""

    ordered = sorted(
        bundles,
        key=lambda item: (
            item.issue_id,
            item.hierarchy_priority,
            -item.relevance_score,
            item.title.casefold(),
            item.reference or "",
            item.evidence_id,
        ),
    )
    selected: list[EvidenceBundle] = []
    rejected: list[tuple[str, str]] = []
    counts: dict[str, int] = {}
    minute_counts: dict[str, int] = {}
    seen: set[tuple[str, str, str, str]] = set()
    for bundle in ordered:
        if not bundle.usable_in_public_response:
            rejected.append((bundle.evidence_id, "source non exploitable publiquement"))
            continue
        key = (
            bundle.issue_id,
            bundle.title.casefold(),
            (bundle.reference or "").casefold(),
            (bundle.excerpt or "").casefold(),
        )
        if key in seen:
            rejected.append((bundle.evidence_id, "doublon documentaire"))
            continue
        if counts.get(bundle.issue_id, 0) >= max_per_issue:
            rejected.append((bundle.evidence_id, "volume maximal atteint pour la question"))
            continue
        if (
            bundle.source_type is EvidenceSourceType.CSE_CSSCT_MINUTES
            and minute_counts.get(bundle.issue_id, 0) >= max_minutes_per_issue
        ):
            rejected.append((bundle.evidence_id, "volume maximal de PV atteint pour la question"))
            continue
        seen.add(key)
        selected.append(bundle)
        counts[bundle.issue_id] = counts.get(bundle.issue_id, 0) + 1
        if bundle.source_type is EvidenceSourceType.CSE_CSSCT_MINUTES:
            minute_counts[bundle.issue_id] = minute_counts.get(bundle.issue_id, 0) + 1
    return EvidenceSelection(tuple(bundles), tuple(selected), tuple(rejected))


__all__ = (
    "EvidenceBundle",
    "EvidenceSelection",
    "EvidenceSourceType",
    "build_evidence_bundles",
    "select_evidence",
)
