"""Concrete coordination for retirement document knowledge."""

from __future__ import annotations

from .career_evidence_models import EvidenceBundle
from .career_timeline_models import CareerTimeline
from .document_context_builder import DocumentContextBuilder
from .document_knowledge_models import (
    ApplicableDocument,
    DocumentSelectionReport,
    DocumentTimeline,
    DocumentVersion,
    KnowledgeContext,
    KnowledgeRequest,
)
from .document_selector import DocumentSelector
from .document_version_resolver import DocumentVersionResolver


class DocumentKnowledgeEngine:
    """Coordinate structural selection, version resolution and context building."""

    def __init__(
        self,
        selector: DocumentSelector | None = None,
        version_resolver: DocumentVersionResolver | None = None,
        context_builder: DocumentContextBuilder | None = None,
    ) -> None:
        self._selector = selector or DocumentSelector()
        self._version_resolver = version_resolver or DocumentVersionResolver()
        self._context_builder = context_builder or DocumentContextBuilder()

    def select_documents(
        self,
        request: KnowledgeRequest,
        candidates: tuple[ApplicableDocument, ...] = (),
    ) -> DocumentSelectionReport:
        return self._selector.select(request, candidates)

    def resolve_document_version(
        self, timeline: DocumentTimeline, applicable_on: str
    ) -> DocumentVersion | None:
        return self._version_resolver.resolve(timeline, applicable_on)

    def build_context(
        self,
        context_id: str,
        timeline: CareerTimeline,
        evidence_bundle: EvidenceBundle,
        employee_question: str,
        request: KnowledgeRequest,
    ) -> KnowledgeContext:
        return self._context_builder.build(
            context_id, timeline, evidence_bundle, employee_question, request
        )


__all__ = ("DocumentKnowledgeEngine",)
