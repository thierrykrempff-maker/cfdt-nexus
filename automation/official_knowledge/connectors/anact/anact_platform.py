"""Inactive Connector Platform composition for ANACT."""
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

from . import ANACT_NETWORK_NOT_IMPLEMENTED

ANACT_METADATA=ConnectorMetadata("anact","ANACT","Agence nationale pour l'amélioration des conditions de travail","Architecture documentaire sans transport",("working_conditions","work_organization","social_dialogue"))
ANACT_CAPABILITIES=frozenset({Capability.MANUAL})
ANACT_PLATFORM_CONTRACT=ConnectorContract(metadata=ANACT_METADATA,state=ConnectorState.ARCHITECTURE_ONLY,capabilities=ANACT_CAPABILITIES,document_policy=DocumentPolicy.METADATA_ONLY,license_id=LicenseId.DOCUMENT_SPECIFIC,security=DEFAULT_SECURITY_POLICY,enabled=False)
ANACT_VALIDATION:ValidationResult=validate_contract(ANACT_PLATFORM_CONTRACT)
ANACT_REGISTRY=ConnectorRegistry();ANACT_REGISTRY.register(ANACT_PLATFORM_CONTRACT)
ANACT_HEALTH=HealthReport(HealthStatus.DISABLED,datetime(2026,7,17,tzinfo=timezone.utc),"architecture_only")
ANACT_STATISTICS=ConnectorStatistics(document_count=0,consultation_count=0,average_duration_ms=0,last_synchronization=None,last_validation=None)
ANACT_METRICS=(Metric("documents",0,"count"),Metric("consultations",0,"count"),Metric("errors",0,"count"),Metric("average_duration",0,"ms"))

def operation_not_implemented()->ConnectorPlatformError:return ConnectorPlatformError(ErrorCode.NETWORK_DISABLED,ANACT_NETWORK_NOT_IMPLEMENTED)
