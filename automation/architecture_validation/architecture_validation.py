"""Deterministic public validation report for the frozen Nexus architecture."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dependency_validation import ARCH_LAYERS, ArchitectureViolation, analyze_architecture_dependencies


@dataclass(frozen=True)
class ArchitectureReport:
    """Stable technical report; it contains no business conclusion."""

    architecture_valid: bool
    modules_present: tuple[str, ...]
    missing_modules: tuple[str, ...]
    dependencies_conform: bool
    boundaries_conform: bool
    violations: tuple[ArchitectureViolation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "architecture_valid": self.architecture_valid,
            "modules_present": list(self.modules_present),
            "missing_modules": list(self.missing_modules),
            "dependencies_conform": self.dependencies_conform,
            "boundaries_conform": self.boundaries_conform,
            "violations": [
                {"code": item.code, "path": item.path, "line": item.line, "message": item.message}
                for item in self.violations
            ],
        }


class ArchitectureValidator:
    """Validate the repository without importing business engines or using the network."""

    def __init__(self, repository_root: Path | None = None) -> None:
        self.repository_root = (repository_root or Path(__file__).resolve().parents[2]).resolve()

    def validate(self) -> ArchitectureReport:
        present: list[str] = []
        missing: list[str] = []
        for layer, package in ARCH_LAYERS.items():
            path = self.repository_root.joinpath(*package.split("."))
            (present if path.is_dir() and (path / "__init__.py").is_file() else missing).append(layer)
        violations = list(analyze_architecture_dependencies(self.repository_root))
        violations.extend(
            ArchitectureViolation("MISSING_ARCH_MODULE", "", 0, f"{layer} package is missing.")
            for layer in missing
        )
        ordered = tuple(sorted(set(violations)))
        dependency_codes = {"FORBIDDEN_ARCH_DEPENDENCY", "HISTORICAL_REVERSE_DEPENDENCY", "CIRCULAR_IMPORT"}
        boundary_codes = {"NETWORK_CALL", "NETWORK_DEPENDENCY", "FORBIDDEN_BOUNDARY_DEPENDENCY"}
        dependencies_conform = not any(item.code in dependency_codes for item in ordered)
        boundaries_conform = not any(item.code in boundary_codes for item in ordered)
        return ArchitectureReport(
            architecture_valid=not missing and not ordered,
            modules_present=tuple(present),
            missing_modules=tuple(missing),
            dependencies_conform=dependencies_conform,
            boundaries_conform=boundaries_conform,
            violations=ordered,
        )


def validate_architecture(repository_root: Path | None = None) -> ArchitectureReport:
    """Return the deterministic ARCH-05 validation report."""
    return ArchitectureValidator(repository_root).validate()
