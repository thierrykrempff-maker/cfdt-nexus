"""Single Connector Platform composition for the inactive CNIL facade."""
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
from automation.connector_platform.connector_validation import ValidationResult as PlatformValidationResult,validate_contract

from . import CNIL_NETWORK_NOT_IMPLEMENTED

CNIL_METADATA=ConnectorMetadata("cnil","CNIL","Commission nationale de l'informatique et des libertés","Contrat documentaire désactivé et sans transport",("privacy","official_guidance"))
CNIL_CAPABILITIES=frozenset({Capability.HTML,Capability.PDF,Capability.OPEN_DATA,Capability.MANUAL})
CNIL_PLATFORM_CONTRACT=ConnectorContract(
 metadata=CNIL_METADATA,state=ConnectorState.ARCHITECTURE_ONLY,capabilities=CNIL_CAPABILITIES,
 document_policy=DocumentPolicy.METADATA_ONLY,license_id=LicenseId.CC_BY_ND,
 security=DEFAULT_SECURITY_POLICY,enabled=False,
)
CNIL_PLATFORM_VALIDATION:PlatformValidationResult=validate_contract(CNIL_PLATFORM_CONTRACT)
CNIL_PLATFORM_REGISTRY=ConnectorRegistry();CNIL_PLATFORM_REGISTRY.register(CNIL_PLATFORM_CONTRACT)
CNIL_HEALTH=HealthReport(HealthStatus.DISABLED,datetime(2026,7,16,tzinfo=timezone.utc),"architecture_only")
CNIL_STATISTICS=ConnectorStatistics(document_count=0,consultation_count=0,average_duration_ms=0,last_synchronization=None,last_validation=None)
CNIL_METRICS=(Metric("documents",0,"count"),Metric("consultations",0,"count"))

def network_not_implemented()->ConnectorPlatformError:
 return ConnectorPlatformError(ErrorCode.NETWORK_DISABLED,CNIL_NETWORK_NOT_IMPLEMENTED)
