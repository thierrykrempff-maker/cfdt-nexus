"""Deterministic metadata-only document-family selection plans."""

from __future__ import annotations

from .document_knowledge_models import (
    ApplicableDocument,
    ContextualDocumentSet,
    DocumentPriority,
    DocumentSelectionReport,
    KnowledgeRequest,
)


_EVENT_DOCUMENT_FAMILIES: dict[str, tuple[str, ...]] = {
    "NIGHT_WORK": (
        "INEOS_NIGHT_WORK_AGREEMENT",
        "CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT",
        "INEOS_WORKING_TIME_AGREEMENT",
        "INEOS_END_OF_CAREER_AGREEMENT",
        "CARSAT_SOURCE",
        "INRS_SOURCE",
        "ANACT_SOURCE",
    ),
    "FIVE_SHIFT": (
        "INEOS_WORKING_TIME_AGREEMENT",
        "CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT",
        "CARSAT_SOURCE",
        "INRS_SOURCE",
    ),
    "WORKPLACE_ACCIDENT": ("SOCIAL_PROTECTION_SOURCE", "CARSAT_SOURCE", "INRS_SOURCE"),
    "OCCUPATIONAL_DISEASE": ("SOCIAL_PROTECTION_SOURCE", "CARSAT_SOURCE", "INRS_SOURCE"),
    "END_OF_CAREER": ("INEOS_END_OF_CAREER_AGREEMENT", "CARSAT_SOURCE"),
    "RETIREMENT": ("CARSAT_SOURCE", "SOCIAL_PROTECTION_SOURCE"),
}


class DocumentSelector:
    """Select declared families and injected document metadata without lookup."""

    def select(
        self,
        request: KnowledgeRequest,
        candidates: tuple[ApplicableDocument, ...] = (),
    ) -> DocumentSelectionReport:
        families: list[str] = list(_EVENT_DOCUMENT_FAMILIES.get(request.event_type or "", ()))
        reasons: list[str] = []
        if request.event_type:
            reasons.append(f"Career event criterion: {request.event_type}")
        additions = (
            (request.night_work, "NIGHT_WORK", _EVENT_DOCUMENT_FAMILIES["NIGHT_WORK"]),
            (request.five_shift_work, "FIVE_SHIFT", _EVENT_DOCUMENT_FAMILIES["FIVE_SHIFT"]),
            (request.atmp_context, "ATMP", _EVENT_DOCUMENT_FAMILIES["WORKPLACE_ACCIDENT"]),
            (request.c2p_context, "C2P", ("C2P_SOURCE", "CARSAT_SOURCE")),
            (request.end_of_career_context, "END_OF_CAREER", _EVENT_DOCUMENT_FAMILIES["END_OF_CAREER"]),
            (request.retirement_context, "RETIREMENT", _EVENT_DOCUMENT_FAMILIES["RETIREMENT"]),
            (request.seniority_context, "SENIORITY", ("CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT", "INEOS_AGREEMENTS_BIBLE")),
        )
        for active, label, document_families in additions:
            if active:
                families.extend(document_families)
                reasons.append(f"Context criterion: {label}")
        if request.classification:
            families.append("CHEMICAL_INDUSTRY_COLLECTIVE_AGREEMENT")
            reasons.append("Classification criterion supplied.")
        if request.work_schedule or request.job_position:
            families.append("INEOS_AGREEMENTS_BIBLE")
            reasons.append("Job position or work schedule criterion supplied.")

        unique_families = tuple(dict.fromkeys(families))
        selected = tuple(
            candidate
            for candidate in candidates
            if not candidate.domains
            or bool(set(candidate.domains) & set(unique_families + ((request.event_type,) if request.event_type else ())))
        )
        document_set = ContextualDocumentSet(
            required=tuple(item for item in selected if item.priority is DocumentPriority.REQUIRED),
            supporting=tuple(item for item in selected if item.priority in {DocumentPriority.HIGH, DocumentPriority.NORMAL}),
            contextual=tuple(item for item in selected if item.priority is DocumentPriority.CONTEXTUAL),
        )
        return DocumentSelectionReport(
            request_id=request.request_id,
            required_document_families=unique_families,
            reasons=tuple(reasons),
            selected_documents=document_set,
            opened_document_ids=(),
            warnings=(
                "Selection is metadata-only and does not establish an individual entitlement.",
                "Individual evidence and provenance remain required.",
            ),
        )
