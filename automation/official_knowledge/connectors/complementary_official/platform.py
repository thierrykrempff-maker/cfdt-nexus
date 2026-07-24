"""Connector Platform registrations for reviewed complementary sources."""

from __future__ import annotations

from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_contract import ConnectorContract
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_metadata import ConnectorMetadata
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_security import DEFAULT_SECURITY_POLICY
from automation.connector_platform.connector_states import ConnectorState
from automation.connector_platform.connector_validation import validate_contract

from .models import ComplementaryConnectorSpec


COMPLEMENTARY_CONNECTOR_SPECS = {
    "defenseur_droits": ComplementaryConnectorSpec(
        "defenseur_droits",
        "Défenseur des droits",
        "Défenseur des droits",
        frozenset({"www.defenseurdesdroits.fr"}),
        "independent_authority",
        ("discrimination", "equality", "employment", "rights"),
    ),
    "ministere_travail": ComplementaryConnectorSpec(
        "ministere_travail",
        "Ministère du Travail",
        "Ministère du Travail",
        frozenset({"travail-emploi.gouv.fr"}),
        "administrative_guidance",
        ("employment_law", "procedures", "official_guidance"),
    ),
    "service_public": ComplementaryConnectorSpec(
        "service_public",
        "Service-Public.fr",
        "Direction de l'information légale et administrative",
        frozenset({"www.service-public.fr"}),
        "official_practical_information",
        ("employee_procedures", "formalities", "practical_information"),
    ),
}


def _contract(spec: ComplementaryConnectorSpec) -> ConnectorContract:
    return ConnectorContract(
        metadata=ConnectorMetadata(
            spec.connector_id,
            spec.display_name,
            spec.publisher,
            "Catalogue public contrôlé, hors ligne et metadata-only",
            spec.tags,
        ),
        state=ConnectorState.VALIDATED,
        capabilities=frozenset({Capability.MANUAL}),
        document_policy=DocumentPolicy.METADATA_ONLY,
        license_id=LicenseId.DOCUMENT_SPECIFIC,
        security=DEFAULT_SECURITY_POLICY,
        enabled=False,
    )


COMPLEMENTARY_CONNECTOR_CONTRACTS = {
    connector_id: _contract(spec)
    for connector_id, spec in COMPLEMENTARY_CONNECTOR_SPECS.items()
}
if not all(
    validate_contract(contract).valid
    for contract in COMPLEMENTARY_CONNECTOR_CONTRACTS.values()
):
    raise ValueError("invalid complementary connector contract")

COMPLEMENTARY_CONNECTOR_REGISTRY = ConnectorRegistry()
for _connector_id in sorted(COMPLEMENTARY_CONNECTOR_CONTRACTS):
    COMPLEMENTARY_CONNECTOR_REGISTRY.register(
        COMPLEMENTARY_CONNECTOR_CONTRACTS[_connector_id]
    )
