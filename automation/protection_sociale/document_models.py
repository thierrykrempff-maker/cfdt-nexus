"""Generic, non-inferential document model for Protection sociale."""
from __future__ import annotations
import uuid
from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = "1.0"
DOCUMENT_DOMAINS = {"mutuelle", "prévoyance", "maintien_salaire", "portabilité", "procédure_interne", "autre"}
DOCUMENT_CATEGORIES = {"notice", "tableau_garanties", "cotisations", "formulaire", "courrier", "procédure", "contrat", "avenant", "FAQ", "tableau", "autre"}

def stable_document_id(source_relative_path: str, source_sha256: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cfdt-nexus:protection-sociale:{source_relative_path}:{source_sha256}:{SCHEMA_VERSION}"))

@dataclass
class ProtectionSocialeDocument:
    document_id: str
    source_relative_path: str
    source_filename: str
    source_extension: str
    source_size_bytes: int
    source_sha256: str
    document_domain: str = "autre"
    document_category: str = "autre"
    document_subcategory: str | None = None
    issuer: str | None = None
    insurer_or_provider: str | None = None
    contract_reference: str | None = None
    effective_date: str | None = None
    expiration_date: str | None = None
    version_date: str | None = None
    document_status: str | None = None
    confidentiality_level: str = "confidentiel_local"
    contains_personal_data_hint: bool = False
    extraction_status: str = "not_started"
    warnings: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return asdict(self)
