"""Abstract metadata-only provider contract for existing local corpora."""

from typing import Protocol

from .document_knowledge_models import ApplicableDocument, DocumentTimeline, KnowledgeRequest
from .document_rule_models import RuleCandidate


class DocumentKnowledgeProvider(Protocol):
    """Future provider boundary; this LOT supplies no implementation."""

    def supported_source_ids(self) -> tuple[str, ...]: ...

    def find_document_candidates(self, request: KnowledgeRequest) -> tuple[ApplicableDocument, ...]: ...

    def get_document_timeline(self, document_family_id: str) -> DocumentTimeline | None: ...

    def find_rule_candidates(self, request: KnowledgeRequest) -> tuple[RuleCandidate, ...]: ...
