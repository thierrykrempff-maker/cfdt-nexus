"""Public ARCH-03 API for common expert facades."""

from .base import (
    FACADE_API_VERSION,
    ExpertFacade,
    FacadeErrorCode,
    LegacyBusinessRefusal,
    MalformedLegacyOutput,
    structured_error_report,
)
from .payroll import PAYROLL_CAPABILITIES, PAYROLL_EXPERT_ID, PAYROLL_FACADE_VERSION, PayrollFacade
from .registry import (
    DuplicateExpertError,
    ExpertFacadeRegistry,
    ExpertRegistration,
    FacadeStatus,
    FacadeUnavailableError,
    UnknownExpertError,
    build_default_registry,
)

__all__ = (
    "DuplicateExpertError",
    "ExpertFacade",
    "ExpertFacadeRegistry",
    "ExpertRegistration",
    "FACADE_API_VERSION",
    "FacadeErrorCode",
    "FacadeStatus",
    "FacadeUnavailableError",
    "LegacyBusinessRefusal",
    "MalformedLegacyOutput",
    "PAYROLL_CAPABILITIES",
    "PAYROLL_EXPERT_ID",
    "PAYROLL_FACADE_VERSION",
    "PayrollFacade",
    "UnknownExpertError",
    "build_default_registry",
    "structured_error_report",
)
