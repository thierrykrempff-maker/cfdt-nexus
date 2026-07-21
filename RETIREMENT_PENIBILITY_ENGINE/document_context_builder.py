"""Build a future document context from existing timeline and evidence IDs."""

from __future__ import annotations

from .career_evidence_models import EvidenceBundle
from .career_timeline_models import CareerTimeline
from .document_knowledge_models import KnowledgeContext, KnowledgeRequest


class DocumentContextBuilder:
    """Prepare lightweight references without searching or opening documents."""

    def build(
        self,
        context_id: str,
        timeline: CareerTimeline,
        evidence_bundle: EvidenceBundle,
        employee_question: str,
        request: KnowledgeRequest,
    ) -> KnowledgeContext:
        return KnowledgeContext(
            context_id=context_id,
            timeline_id=timeline.timeline_id,
            event_ids=tuple(event.event_id for event in timeline.events),
            evidence_bundle_id=evidence_bundle.bundle_id,
            evidence_ids=tuple(str(item.reference.evidence_id) for item in evidence_bundle.evidence),
            question=employee_question,
            request=request,
            synthetic_only=timeline.synthetic_only and evidence_bundle.synthetic_only,
        )
