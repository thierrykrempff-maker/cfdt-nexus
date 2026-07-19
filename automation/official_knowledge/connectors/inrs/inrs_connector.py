"""Public architecture-only facade for the future official INRS connector."""

from __future__ import annotations

from .inrs_contract import INRS_DOCUMENT_CONTRACT, InrsDocumentRegistryPort
from .inrs_models import InrsDocumentIdentity
from .inrs_platform import (
    INRS_CAPABILITIES, INRS_HEALTH, INRS_METRICS, INRS_OFFICIAL_DOMAINS,
    INRS_PLATFORM_CONTRACT, INRS_REGISTRY, INRS_STATISTICS, INRS_VALIDATION,
    network_not_implemented,
)


class InrsConnector:
    """Inactive connector description; every operational method fails closed."""

    platform_contract=INRS_PLATFORM_CONTRACT;platform_registry=INRS_REGISTRY
    platform_validation=INRS_VALIDATION;capabilities=INRS_CAPABILITIES
    health=INRS_HEALTH;statistics=INRS_STATISTICS;metrics=INRS_METRICS
    document_contract=INRS_DOCUMENT_CONTRACT;official_domains=INRS_OFFICIAL_DOMAINS
    enabled=platform_contract.enabled;connector_status=platform_contract.state.value
    def __init__(self,*,document_registry:InrsDocumentRegistryPort|None=None):self.document_registry=document_registry
    @property
    def document_registry_compatible(self)->bool:return True
    def serialize_identity(self,identity:InrsDocumentIdentity)->dict:return identity.to_dict()
    def deserialize_identity(self,value:dict)->InrsDocumentIdentity:return InrsDocumentIdentity.from_dict(value)
    def discover(self,_scope:str):raise network_not_implemented()
    def fetch(self,_identity:InrsDocumentIdentity):raise network_not_implemented()
    def synchronize(self):raise network_not_implemented()
