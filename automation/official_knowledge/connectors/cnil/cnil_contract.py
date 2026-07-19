"""Document policy and common registry interface for CNIL LOT 0."""

from dataclasses import dataclass
from typing import Protocol

from automation.official_knowledge.document_registry import DocumentChange, DocumentRecord


@dataclass(frozen=True)
class CnilDocumentContract:
    policy: str = "METADATA_ONLY"
    text_indexing_allowed: bool = False
    local_copy_allowed: bool = False
    pdf_allowed: bool = False
    html_extraction_allowed: bool = False
    provenance_required: bool = True
    citation_required: bool = True
    https_required: bool = True

    def __post_init__(self) -> None:
        if self.policy != "METADATA_ONLY":
            raise ValueError("CNIL document policy must be METADATA_ONLY")
        forbidden = (
            self.text_indexing_allowed,
            self.local_copy_allowed,
            self.pdf_allowed,
            self.html_extraction_allowed,
        )
        if any(forbidden):
            raise ValueError("CNIL LOT 0 forbids content collection and storage")
        required = (self.provenance_required, self.citation_required, self.https_required)
        if not all(required):
            raise ValueError("provenance, citation and HTTPS are mandatory")


class CnilDocumentRegistryPort(Protocol):
    """Structural interface only; LOT 0 never instantiates persistence."""

    def register_document(self, document: DocumentRecord) -> DocumentChange: ...

    def update_document(self, document: DocumentRecord) -> DocumentChange: ...

    def find_document(self, document_id: str) -> DocumentRecord | None: ...


CNIL_DOCUMENT_CONTRACT = CnilDocumentContract()
