"""Metadata-only adapter for declarative INEOS agreement records."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

from .ingestion_models import (
    AgreementMetadataInput,
    AgreementNature,
    ExplicitDocumentLink,
    MetadataStatus,
)
from .models import RelationKind


_NATURES = {
    "accord": AgreementNature.AGREEMENT,
    "accord_entreprise": AgreementNature.AGREEMENT,
    "avenant": AgreementNature.AMENDMENT,
    "protocole": AgreementNature.PROTOCOL,
    "decision_unilaterale": AgreementNature.UNILATERAL_DECISION,
    "règlement_intérieur": AgreementNature.INTERNAL_REGULATION,
    "reglement_interieur": AgreementNature.INTERNAL_REGULATION,
}
_STATUSES = {
    "active": MetadataStatus.ACTIVE,
    "actif": MetadataStatus.ACTIVE,
    "replaced": MetadataStatus.REPLACED,
    "remplace": MetadataStatus.REPLACED,
    "remplacé": MetadataStatus.REPLACED,
    "expired": MetadataStatus.EXPIRED,
    "expire": MetadataStatus.EXPIRED,
    "expiré": MetadataStatus.EXPIRED,
    "unknown": MetadataStatus.UNKNOWN,
    "inconnu": MetadataStatus.UNKNOWN,
}
_RELATIONS = {
    "replaces": RelationKind.SUPERSEDES,
    "remplace": RelationKind.SUPERSEDES,
    "amends": RelationKind.AMENDS,
    "modifie": RelationKind.AMENDS,
    "completes": RelationKind.IMPLEMENTS,
    "complète": RelationKind.IMPLEMENTS,
    "complete": RelationKind.IMPLEMENTS,
    "annex": RelationKind.RELATED_TO,
    "annexe": RelationKind.RELATED_TO,
}


def stable_agreement_id(
    agreement_reference: str,
    family: str,
    version: str | None,
) -> str:
    material = "\n".join(
        (
            agreement_reference.strip().lower(),
            family.strip().lower(),
            (version or "").strip().lower(),
        )
    ).encode("utf-8")
    return f"agreement-{sha256(material).hexdigest()}"


class INEOSAgreementMetadataAdapter:
    """Map normalized agreement metadata and ignore storage-related fields."""

    def adapt(self, metadata: Mapping[str, Any]) -> AgreementMetadataInput:
        title = str(metadata.get("title") or metadata.get("normalized_title") or "").strip()
        reference = str(
            metadata.get("agreement_reference")
            or metadata.get("reference")
            or metadata.get("document_id")
            or ""
        ).strip()
        family = str(metadata.get("family") or metadata.get("primary_topic") or "").strip()
        if not title or not reference or not family:
            raise ValueError(
                "AGREEMENT_METADATA_INCOMPLETE: title, reference and family are required"
            )
        version = (
            str(metadata["version"]).strip()
            if metadata.get("version") is not None
            else None
        )
        raw_nature = str(
            metadata.get("nature") or metadata.get("document_type") or "accord"
        ).strip().lower()
        raw_status = str(metadata.get("status") or "unknown").strip().lower()
        parent_link = None
        parent_reference = metadata.get("parent_reference")
        if parent_reference:
            parent_family = str(metadata.get("parent_family") or family)
            parent_version = (
                str(metadata["parent_version"])
                if metadata.get("parent_version") is not None
                else None
            )
            relation_name = str(metadata.get("parent_relation") or "amends").lower()
            relation_kind = _RELATIONS.get(relation_name)
            if relation_kind is None:
                raise ValueError("AGREEMENT_RELATION_INVALID")
            parent_link = ExplicitDocumentLink(
                target_document_id=stable_agreement_id(
                    str(parent_reference),
                    parent_family,
                    parent_version,
                ),
                relation_kind=relation_kind,
            )
        secondary_topics = metadata.get("secondary_topics") or ()
        if isinstance(secondary_topics, str):
            secondary_topics = (secondary_topics,)
        return AgreementMetadataInput(
            pseudonymous_id=stable_agreement_id(reference, family, version),
            normalized_title=title,
            logical_provenance="INEOS_AGREEMENT_METADATA",
            nature=_NATURES.get(raw_nature, AgreementNature.OTHER),
            family=family,
            agreement_reference=reference,
            version=version,
            signature_date=metadata.get("signature_date"),
            effective_from=metadata.get("effective_from"),
            effective_to=metadata.get("effective_to"),
            status=_STATUSES.get(raw_status, MetadataStatus.UNKNOWN),
            parent_link=parent_link,
            confidence=float(metadata.get("confidence", 1.0)),
            topics=tuple(str(item) for item in secondary_topics),
        )
