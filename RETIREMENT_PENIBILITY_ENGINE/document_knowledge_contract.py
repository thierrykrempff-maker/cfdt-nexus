"""Implementation-independent contract for retirement document knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_evidence_models import EvidenceBundle
from .career_timeline_models import CareerTimeline
from .document_knowledge_models import (
    ApplicableDocument,
    DocumentSelectionReport,
    DocumentTimeline,
    DocumentVersion,
    KnowledgeContext,
    KnowledgeRequest,
)


@dataclass(frozen=True)
class DocumentKnowledgeSafetyContract:
    """Safety declaration for a provider-free architecture lot."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    provider_implemented: bool = False
    corpus_access_allowed: bool = False
    network_allowed: bool = False
    scraping_allowed: bool = False
    pdf_allowed: bool = False
    indexing_allowed: bool = False
    parsing_allowed: bool = False
    artificial_intelligence_allowed: bool = False
    retirement_calculation_allowed: bool = False


DOCUMENT_KNOWLEDGE_SAFETY_CONTRACT = DocumentKnowledgeSafetyContract()


class DocumentKnowledgePort(Protocol):
    """Stable operations implemented by ``DocumentKnowledgeEngine``."""

    def select_documents(
        self,
        request: KnowledgeRequest,
        candidates: tuple[ApplicableDocument, ...] = (),
    ) -> DocumentSelectionReport: ...

    def resolve_document_version(
        self, timeline: DocumentTimeline, applicable_on: str
    ) -> DocumentVersion | None: ...

    def build_context(
        self,
        context_id: str,
        timeline: CareerTimeline,
        evidence_bundle: EvidenceBundle,
        employee_question: str,
        request: KnowledgeRequest,
    ) -> KnowledgeContext: ...


__all__ = (
    "DocumentKnowledgePort",
    "DOCUMENT_KNOWLEDGE_SAFETY_CONTRACT",
)
