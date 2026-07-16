"""Connector Platform composition for DREETS Grand Est.

Everything in this module is declarative and offline.  It preserves the public
DREETS facade while making Connector Platform the single source of truth.
"""
from datetime import datetime,timezone

from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_contract import ConnectorContract
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ConnectorPlatformError,ErrorCode
from automation.connector_platform.connector_health import HealthReport,HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_metadata import ConnectorMetadata
from automation.connector_platform.connector_metrics import Metric
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_security import DEFAULT_SECURITY_POLICY
from automation.connector_platform.connector_states import ConnectorState
from automation.connector_platform.connector_statistics import ConnectorStatistics
from automation.connector_platform.connector_validation import ValidationResult,validate_contract

from . import DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED

DREETS_METADATA=ConnectorMetadata(
 "dreets_grand_est","DREETS Grand Est","Direction régionale de l'économie, de l'emploi, du travail et des solidarités",
 "Contrat documentaire désactivé et sans transport",("official_guidance","grand_est"),
)
DREETS_CAPABILITIES=frozenset({Capability.HTML,Capability.RSS,Capability.SITEMAP,Capability.PDF,Capability.MANUAL})
DREETS_PLATFORM_CONTRACT=ConnectorContract(
 metadata=DREETS_METADATA,state=ConnectorState.ARCHITECTURE_ONLY,capabilities=DREETS_CAPABILITIES,
 document_policy=DocumentPolicy.METADATA_ONLY,license_id=LicenseId.UNKNOWN,
 security=DEFAULT_SECURITY_POLICY,enabled=False,
)
DREETS_VALIDATION:ValidationResult=validate_contract(DREETS_PLATFORM_CONTRACT)
DREETS_REGISTRY=ConnectorRegistry();DREETS_REGISTRY.register(DREETS_PLATFORM_CONTRACT)
DREETS_HEALTH=HealthReport(HealthStatus.DISABLED,datetime(2026,7,16,tzinfo=timezone.utc),"architecture_only")
DREETS_STATISTICS=ConnectorStatistics(document_count=0,consultation_count=0,average_duration_ms=0,last_synchronization=None,last_validation=None)
DREETS_METRICS=(Metric("documents",0,"count"),Metric("consultations",0,"count"))

def network_not_implemented()->ConnectorPlatformError:
 return ConnectorPlatformError(ErrorCode.NETWORK_DISABLED,DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED)
