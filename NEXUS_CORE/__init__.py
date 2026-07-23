"""Public, engine-neutral domain language for CFDT Nexus V3."""

from .analysis import (
    AnalysisQuestion,
    AnalysisReport,
    AnalysisRequest,
    AnalysisScope,
    AnalysisStatus,
    DomainAnalysisResult,
    DomainResultReference,
    DomainSelection,
)
from .conflicts import (
    ConflictReason,
    ConflictResolutionReference,
    ConflictStatus,
    EvidenceConflict,
)
from .contracts import (
    DomainAnalyzer,
    DomainResultAdapter,
    EvidenceProducer,
    FindingProducer,
    RecommendationProducer,
)
from .documents import DocumentMetadata, DocumentReference, DocumentSource, DocumentType
from .entities import (
    EmployerReference,
    EmploymentPeriod,
    EmploymentReference,
    EntityReference,
    PersonReference,
)
from .evidence import Evidence
from .findings import Finding, FindingSeverity, FindingStatus, FindingType
from .identifiers import (
    AnalysisId,
    ConflictId,
    CorrelationId,
    DocumentId,
    EntityId,
    EvidenceId,
    FindingId,
    RecommendationId,
)
from .periods import Period, PeriodPrecision, PeriodStatus
from .privacy import (
    ConfidentialityLevel,
    DataSensitivity,
    Diagnostic,
    MetadataEntry,
    RedactionStatus,
)
from .provenance import AcquisitionMethod, Provenance, SourceReference, SourceType
from .quality import ConfidenceLevel, ConfidenceScore, EvidenceQuality, ValidationStatus
from .recommendations import (
    Recommendation,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
)
from .serialization import to_json, to_primitive
from .values import (
    BooleanEvidenceValue,
    CustomEvidenceValue,
    EntityEvidenceValue,
    EvidenceValue,
    NumericEvidenceValue,
    TemporalEvidenceValue,
    TextEvidenceValue,
)

__all__ = [name for name in globals() if not name.startswith("_")]
