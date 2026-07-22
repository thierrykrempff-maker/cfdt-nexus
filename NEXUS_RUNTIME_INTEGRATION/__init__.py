"""Progressive, fail-safe bridge from the historical Runtime to Nexus Core V3."""

from .config import RuntimeConnectorConfig, RuntimeIntegrationConfig
from .connector_mapper import RuntimeConnectorMappingResult, RuntimeConnectorPayloadMapper
from .integration import RuntimeCoreIntegration
from .mappers import RuntimeExpertPayloadMapper
from .models import (
    RuntimeCoreIntegrationDiagnostics,
    RuntimeCoreIntegrationInput,
    RuntimeCoreIntegrationResult,
    RuntimeMode,
)
from .report_mapper import RuntimeCoreReportMapper

__all__ = (
    "RuntimeCoreIntegration",
    "RuntimeCoreIntegrationDiagnostics",
    "RuntimeCoreIntegrationInput",
    "RuntimeCoreIntegrationResult",
    "RuntimeCoreReportMapper",
    "RuntimeConnectorConfig",
    "RuntimeConnectorMappingResult",
    "RuntimeConnectorPayloadMapper",
    "RuntimeExpertPayloadMapper",
    "RuntimeIntegrationConfig",
    "RuntimeMode",
)
