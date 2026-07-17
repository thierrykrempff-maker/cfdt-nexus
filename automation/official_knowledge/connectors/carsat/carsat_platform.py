"""Single inactive Connector Platform composition for CARSAT."""
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

from . import CARSAT_NETWORK_NOT_IMPLEMENTED

CARSAT_METADATA=ConnectorMetadata("carsat","CARSAT","Caisse d'assurance retraite et de la santé au travail","Architecture documentaire sans transport",("occupational_risk_prevention","retirement","social_service"))
CARSAT_CAPABILITIES=frozenset({Capability.MANUAL})
CARSAT_PLATFORM_CONTRACT=ConnectorContract(
 metadata=CARSAT_METADATA,state=ConnectorState.ARCHITECTURE_ONLY,capabilities=CARSAT_CAPABILITIES,
 document_policy=DocumentPolicy.METADATA_ONLY,license_id=LicenseId.DOCUMENT_SPECIFIC,
 security=DEFAULT_SECURITY_POLICY,enabled=False,
)
CARSAT_VALIDATION:ValidationResult=validate_contract(CARSAT_PLATFORM_CONTRACT)
CARSAT_REGISTRY=ConnectorRegistry();CARSAT_REGISTRY.register(CARSAT_PLATFORM_CONTRACT)
CARSAT_HEALTH=HealthReport(HealthStatus.DISABLED,datetime(2026,7,17,tzinfo=timezone.utc),"architecture_only")
CARSAT_STATISTICS=ConnectorStatistics(document_count=0,consultation_count=0,average_duration_ms=0,last_synchronization=None,last_validation=None)
CARSAT_METRICS=(Metric("documents",0,"count"),Metric("consultations",0,"count"),Metric("errors",0,"count"),Metric("average_duration",0,"ms"))

def network_not_implemented()->ConnectorPlatformError:
 return ConnectorPlatformError(ErrorCode.NETWORK_DISABLED,CARSAT_NETWORK_NOT_IMPLEMENTED)
