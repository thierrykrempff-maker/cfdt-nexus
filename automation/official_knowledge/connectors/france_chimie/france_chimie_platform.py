"""Inactive Connector Platform composition for France Chimie."""

from datetime import datetime, timezone

from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_contract import ConnectorContract
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ConnectorPlatformError, ErrorCode
from automation.connector_platform.connector_health import HealthReport, HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_metadata import ConnectorMetadata
from automation.connector_platform.connector_metrics import Metric
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_security import DEFAULT_SECURITY_POLICY
from automation.connector_platform.connector_states import ConnectorState
from automation.connector_platform.connector_statistics import ConnectorStatistics
from automation.connector_platform.connector_validation import ValidationResult, validate_contract

from .france_chimie_catalog import FRANCE_CHIMIE_ACTIVE_DOMAINS


FRANCE_CHIMIE_NETWORK_NOT_IMPLEMENTED = "FRANCE_CHIMIE_CONNECTOR_NETWORK_NOT_IMPLEMENTED"
FRANCE_CHIMIE_OFFICIAL_DOMAINS = FRANCE_CHIMIE_ACTIVE_DOMAINS
FRANCE_CHIMIE_METADATA = ConnectorMetadata(
    "france_chimie",
    "France Chimie",
    "France Chimie",
    "Architecture documentaire hors ligne sans transport",
    ("chemical_industry", "occupational_health", "social_dialogue"),
)
FRANCE_CHIMIE_CAPABILITIES = frozenset({Capability.MANUAL})
FRANCE_CHIMIE_PLATFORM_CONTRACT = ConnectorContract(
    metadata=FRANCE_CHIMIE_METADATA,
    state=ConnectorState.ARCHITECTURE_ONLY,
    capabilities=FRANCE_CHIMIE_CAPABILITIES,
    document_policy=DocumentPolicy.METADATA_ONLY,
    license_id=LicenseId.DOCUMENT_SPECIFIC,
    security=DEFAULT_SECURITY_POLICY,
    enabled=False,
)
FRANCE_CHIMIE_VALIDATION: ValidationResult = validate_contract(FRANCE_CHIMIE_PLATFORM_CONTRACT)
FRANCE_CHIMIE_REGISTRY = ConnectorRegistry()
FRANCE_CHIMIE_REGISTRY.register(FRANCE_CHIMIE_PLATFORM_CONTRACT)
FRANCE_CHIMIE_HEALTH = HealthReport(
    HealthStatus.DISABLED,
    datetime(2026, 7, 21, tzinfo=timezone.utc),
    "architecture_only",
)
FRANCE_CHIMIE_STATISTICS = ConnectorStatistics()
FRANCE_CHIMIE_METRICS = (
    Metric("documents", 0, "count"),
    Metric("consultations", 0, "count"),
    Metric("errors", 0, "count"),
    Metric("average_duration", 0, "ms"),
)


def network_not_implemented() -> ConnectorPlatformError:
    return ConnectorPlatformError(ErrorCode.NETWORK_DISABLED, FRANCE_CHIMIE_NETWORK_NOT_IMPLEMENTED)
