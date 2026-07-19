"""Static dependency and boundary validation for the stable ARCH layers."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ARCH_LAYERS = {
    "ARCH-01": "automation.contracts",
    "ARCH-02": "automation.adapters",
    "ARCH-03": "automation.expert_facades",
    "ARCH-04": "automation.orchestrator_common",
}

ALLOWED_ARCH_DEPENDENCIES = {
    "ARCH-01": frozenset(),
    "ARCH-02": frozenset({"ARCH-01"}),
    "ARCH-03": frozenset({"ARCH-01", "ARCH-02"}),
    "ARCH-04": frozenset({"ARCH-01", "ARCH-03"}),
}

NETWORK_MODULES = ("requests", "urllib", "http.client", "socket", "httpx", "aiohttp")
FORBIDDEN_BOUNDARY_MODULES = (
    "automation.connector_platform",
    "automation.connectors",
    "automation.api",
    "automation.routes",
    "apps",
    "cockpit",
)


@dataclass(frozen=True, order=True)
class ArchitectureViolation:
    """One safe, stable and sortable architecture violation."""

    code: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class ModuleAnalysis:
    module: str
    path: str
    imports: tuple[str, ...]


def analyze_architecture_dependencies(repository_root: Path) -> tuple[ArchitectureViolation, ...]:
    """Validate layer direction, boundaries, network use and import cycles."""
    root = repository_root.resolve()
    analyses: list[ModuleAnalysis] = []
    violations: list[ArchitectureViolation] = []
    for layer, package in ARCH_LAYERS.items():
        package_dir = root.joinpath(*package.split("."))
        for path in _production_python_files(package_dir):
            analysis, parse_violations = _analyze_file(path, root)
            analyses.append(analysis)
            violations.extend(parse_violations)
            violations.extend(_validate_imports(analysis, layer))
    violations.extend(_validate_historical_direction(root))
    violations.extend(_find_cycles(analyses))
    return tuple(sorted(set(violations)))


def _production_python_files(directory: Path) -> tuple[Path, ...]:
    if not directory.is_dir():
        return ()
    return tuple(sorted(path for path in directory.rglob("*.py") if not path.name.startswith("test_")))


def _module_name(path: Path, root: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _analyze_file(path: Path, root: Path) -> tuple[ModuleAnalysis, tuple[ArchitectureViolation, ...]]:
    relative = path.relative_to(root).as_posix()
    module = _module_name(path, root)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    except (OSError, SyntaxError) as exc:
        return ModuleAnalysis(module, relative, ()), (
            ArchitectureViolation("UNREADABLE_MODULE", relative, getattr(exc, "lineno", 0) or 0, "Module cannot be analyzed."),
        )
    imports: list[str] = []
    violations: list[ArchitectureViolation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            target = _resolve_import(module, path.name == "__init__.py", node.level, node.module)
            if target:
                imports.append(target)
        elif isinstance(node, ast.Call) and _is_network_call(node.func):
            violations.append(ArchitectureViolation(
                "NETWORK_CALL", relative, node.lineno, "Network call is forbidden in ARCH layers."
            ))
    return ModuleAnalysis(module, relative, tuple(sorted(set(imports)))), tuple(violations)


def _resolve_import(module: str, is_package: bool, level: int, imported: str | None) -> str:
    if level == 0:
        return imported or ""
    base = module.split(".") if is_package else module.split(".")[:-1]
    keep = max(0, len(base) - level + 1)
    parts = base[:keep]
    if imported:
        parts.extend(imported.split("."))
    return ".".join(parts)


def _layer_for_module(module: str) -> str | None:
    for layer, package in ARCH_LAYERS.items():
        if module == package or module.startswith(package + "."):
            return layer
    return None


def _validate_imports(analysis: ModuleAnalysis, source_layer: str) -> tuple[ArchitectureViolation, ...]:
    violations: list[ArchitectureViolation] = []
    for imported in analysis.imports:
        target_layer = _layer_for_module(imported)
        if target_layer and target_layer != source_layer and target_layer not in ALLOWED_ARCH_DEPENDENCIES[source_layer]:
            violations.append(ArchitectureViolation(
                "FORBIDDEN_ARCH_DEPENDENCY", analysis.path, 0,
                f"{source_layer} must not depend on {target_layer}.",
            ))
        if _matches_prefix(imported, NETWORK_MODULES):
            violations.append(ArchitectureViolation(
                "NETWORK_DEPENDENCY", analysis.path, 0,
                f"Network dependency is forbidden in ARCH layers: {imported}.",
            ))
        if _matches_prefix(imported, FORBIDDEN_BOUNDARY_MODULES):
            violations.append(ArchitectureViolation(
                "FORBIDDEN_BOUNDARY_DEPENDENCY", analysis.path, 0,
                f"Connector or endpoint dependency is forbidden in ARCH layers: {imported}.",
            ))
    return tuple(violations)


def _matches_prefix(module: str, prefixes: Iterable[str]) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)


def _is_network_call(function: ast.expr) -> bool:
    name = _qualified_name(function)
    return name == "urlopen" or _matches_prefix(name, NETWORK_MODULES)


def _qualified_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _validate_historical_direction(root: Path) -> tuple[ArchitectureViolation, ...]:
    experts_dir = root / "automation" / "experts"
    violations: list[ArchitectureViolation] = []
    for path in _production_python_files(experts_dir):
        analysis, parse_violations = _analyze_file(path, root)
        violations.extend(parse_violations)
        for imported in analysis.imports:
            if _layer_for_module(imported):
                violations.append(ArchitectureViolation(
                    "HISTORICAL_REVERSE_DEPENDENCY", analysis.path, 0,
                    "Historical experts must not depend directly on ARCH layers.",
                ))
    return tuple(violations)


def _find_cycles(analyses: list[ModuleAnalysis]) -> tuple[ArchitectureViolation, ...]:
    modules = {item.module for item in analyses}
    graph = {
        item.module: tuple(sorted(target for target in item.imports if target in modules))
        for item in analyses
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: set[tuple[str, ...]] = set()

    def visit(module: str) -> None:
        if module in visited:
            return
        if module in visiting:
            start = stack.index(module)
            cycle = tuple(stack[start:] + [module])
            cycles.add(_canonical_cycle(cycle))
            return
        visiting.add(module)
        stack.append(module)
        for target in graph.get(module, ()):
            visit(target)
        stack.pop()
        visiting.remove(module)
        visited.add(module)

    for module in sorted(graph):
        visit(module)
    return tuple(
        ArchitectureViolation("CIRCULAR_IMPORT", "", 0, " -> ".join(cycle))
        for cycle in sorted(cycles)
    )


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    body = cycle[:-1]
    rotations = [body[index:] + body[:index] for index in range(len(body))]
    canonical = min(rotations)
    return canonical + (canonical[0],)
