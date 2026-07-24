"""Progressive, fail-safe bridge from the historical Runtime to Nexus Core V3."""

from .config import (
    RuntimeCSEMemoryConfig,
    RuntimeConnectorConfig,
    RuntimeIntegrationConfig,
    RuntimeOfficialConnectorsConfig,
    RuntimeProtectionSocialeConfig,
    RuntimeRetirementConfig,
    RuntimeSyndicalReasoningConfig,
    RuntimeExpertPaieV2Config,
)
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
from .cse_memory_runtime import (
    RuntimeCSEMemoryDiagnostics,
    RuntimeCSEMemoryIntegration,
    RuntimeCSEMemoryMode,
    RuntimeCSEMemoryResult,
)
from .report_mapper import RuntimeCSEMemoryReportMapper
from .retirement_runtime import (
    RuntimeRetirementDiagnostics,
    RuntimeRetirementIntegration,
    RuntimeRetirementMode,
    RuntimeRetirementResult,
    needs_retirement,
)
from .report_mapper import RuntimeRetirementReportMapper
from .protection_sociale_search import (
    ProtectionSocialeMetadataDocument,
    ProtectionSocialeSearchResult,
    RuntimeProtectionSocialeGateway,
)
from .protection_sociale_runtime import (
    RuntimeProtectionSocialeDiagnostics,
    RuntimeProtectionSocialeIntegration,
    RuntimeProtectionSocialeMapper,
    RuntimeProtectionSocialeMode,
    RuntimeProtectionSocialeResult,
    needs_protection_sociale,
)
from .report_mapper import RuntimeProtectionSocialeReportMapper
from .official_connectors_runtime import (
    RuntimeOfficialConnectorsDiagnostics,
    RuntimeOfficialConnectorsIntegration,
    RuntimeOfficialConnectorsResult,
)
from .public_payload import sanitize_public_payload
from .syndical_reasoning_runtime import (
    RuntimeSyndicalReasoningDiagnostics,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
    RuntimeSyndicalReasoningResult,
    needs_syndical_reasoning,
)
from .report_mapper import RuntimeSyndicalReasoningReportMapper
from .expert_paie_v2_runtime import (
    RuntimeExpertPaieV2Diagnostics,
    RuntimeExpertPaieV2Integration,
    RuntimeExpertPaieV2Mode,
    RuntimeExpertPaieV2Result,
    needs_expert_paie_v2,
)

__all__ = (
    "RuntimeCoreIntegration",
    "RuntimeCoreIntegrationDiagnostics",
    "RuntimeCoreIntegrationInput",
    "RuntimeCoreIntegrationResult",
    "RuntimeCoreReportMapper",
    "RuntimeConnectorConfig",
    "RuntimeConnectorMappingResult",
    "RuntimeConnectorPayloadMapper",
    "RuntimeCSEMemoryConfig",
    "RuntimeCSEMemoryDiagnostics",
    "RuntimeCSEMemoryIntegration",
    "RuntimeCSEMemoryMode",
    "RuntimeCSEMemoryReportMapper",
    "RuntimeCSEMemoryResult",
    "RuntimeExpertPayloadMapper",
    "RuntimeExpertPaieV2Config",
    "RuntimeExpertPaieV2Diagnostics",
    "RuntimeExpertPaieV2Integration",
    "RuntimeExpertPaieV2Mode",
    "RuntimeExpertPaieV2Result",
    "RuntimeIntegrationConfig",
    "RuntimeOfficialConnectorsConfig",
    "RuntimeOfficialConnectorsDiagnostics",
    "RuntimeOfficialConnectorsIntegration",
    "RuntimeOfficialConnectorsResult",
    "RuntimeMode",
    "ProtectionSocialeMetadataDocument",
    "ProtectionSocialeSearchResult",
    "RuntimeProtectionSocialeConfig",
    "RuntimeProtectionSocialeDiagnostics",
    "RuntimeProtectionSocialeGateway",
    "RuntimeProtectionSocialeIntegration",
    "RuntimeProtectionSocialeMapper",
    "RuntimeProtectionSocialeMode",
    "RuntimeProtectionSocialeReportMapper",
    "RuntimeProtectionSocialeResult",
    "RuntimeRetirementConfig",
    "RuntimeRetirementDiagnostics",
    "RuntimeRetirementIntegration",
    "RuntimeRetirementMode",
    "RuntimeRetirementReportMapper",
    "RuntimeRetirementResult",
    "RuntimeSyndicalReasoningConfig",
    "RuntimeSyndicalReasoningDiagnostics",
    "RuntimeSyndicalReasoningIntegration",
    "RuntimeSyndicalReasoningMode",
    "RuntimeSyndicalReasoningReportMapper",
    "RuntimeSyndicalReasoningResult",
    "sanitize_public_payload",
    "needs_retirement",
    "needs_protection_sociale",
    "needs_syndical_reasoning",
    "needs_expert_paie_v2",
)
