"""Public API for the deterministic ARCH-05 architecture validator."""

from .architecture_validation import ArchitectureReport, ArchitectureValidator, validate_architecture
from .dependency_validation import ArchitectureViolation

__all__ = (
    "ArchitectureReport",
    "ArchitectureValidator",
    "ArchitectureViolation",
    "validate_architecture",
)
