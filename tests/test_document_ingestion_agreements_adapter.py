import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    AgreementNature,
    INEOSAgreementMetadataAdapter,
    MetadataStatus,
    RelationKind,
    stable_agreement_id,
)


def _agreement(**changes):
    value = {
        "title": "Accord synthétique sur le temps de travail",
        "agreement_reference": "ACC-TT",
        "family": "working-time",
        "version": "2",
        "nature": "avenant",
        "status": "active",
        "signature_date": "2026-01-15",
        "effective_from": "2026-02-01",
        "parent_reference": "ACC-TT",
        "parent_version": "1",
        "parent_relation": "remplace",
        "relative_path": r"C:\ignored\agreement.pdf",
        "sha256": "ignored-storage-hash",
    }
    value.update(changes)
    return value


def test_agreement_adapter_maps_declarative_metadata_only() -> None:
    item = INEOSAgreementMetadataAdapter().adapt(_agreement())
    assert item.nature is AgreementNature.AMENDMENT
    assert item.status is MetadataStatus.ACTIVE
    assert item.parent_link.relation_kind is RelationKind.SUPERSEDES
    assert item.pseudonymous_id == stable_agreement_id(
        "ACC-TT", "working-time", "2"
    )
    assert "ignored" not in repr(item)


def test_agreement_adapter_identity_is_stable() -> None:
    adapter = INEOSAgreementMetadataAdapter()
    assert adapter.adapt(_agreement()).pseudonymous_id == adapter.adapt(
        _agreement()
    ).pseudonymous_id


def test_agreement_adapter_refuses_missing_required_metadata() -> None:
    with pytest.raises(ValueError, match="AGREEMENT_METADATA_INCOMPLETE"):
        INEOSAgreementMetadataAdapter().adapt({"title": "Accord incomplet"})


def test_agreement_adapter_refuses_unknown_parent_relation() -> None:
    with pytest.raises(ValueError, match="AGREEMENT_RELATION_INVALID"):
        INEOSAgreementMetadataAdapter().adapt(
            _agreement(parent_relation="semantic_guess")
        )
