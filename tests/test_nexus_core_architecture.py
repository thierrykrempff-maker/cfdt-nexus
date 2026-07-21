"""Static architecture guards for the autonomous Nexus Core package."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "NEXUS_CORE"
CORE_FILES = tuple(sorted(CORE.glob("*.py")))


def parsed_files():
    return [(path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path))) for path in CORE_FILES]


def imported_roots(tree):
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_core_has_no_dependency_on_existing_engines_connectors_or_web_frameworks():
    forbidden = {
        "RETIREMENT_PENIBILITY_ENGINE",
        "CCSEMEMORYENGINE",
        "PROTECTION_SOCIALE_ENGINE",
        "automation",
        "apps",
        "flask",
        "fastapi",
        "django",
    }
    for path, tree in parsed_files():
        assert not imported_roots(tree) & forbidden, path.name


def test_core_has_no_network_imports_or_dynamic_imports():
    network = {"socket", "ssl", "http", "urllib", "requests", "httpx", "aiohttp"}
    for path, tree in parsed_files():
        assert not imported_roots(tree) & network, path.name
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        assert not any(
            isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}
            for node in calls
        ), path.name


def test_internal_import_graph_is_acyclic():
    modules = {path.stem for path in CORE_FILES}
    graph = {module: set() for module in modules}
    for path, tree in parsed_files():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                target = node.module.split(".")[0]
                if target in modules:
                    graph[path.stem].add(target)

    visiting = set()
    visited = set()

    def visit(module):
        if module in visiting:
            raise AssertionError(f"import cycle involving {module}")
        if module in visited:
            return
        visiting.add(module)
        for dependency in graph[module]:
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in graph:
        visit(module)


def test_all_core_sources_parse_with_python_3_10_grammar():
    for path in CORE_FILES:
        ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
            feature_version=(3, 10),
        )


def test_core_package_is_small_and_explicit():
    expected = {
        "__init__.py",
        "analysis.py",
        "conflicts.py",
        "contracts.py",
        "documents.py",
        "entities.py",
        "evidence.py",
        "findings.py",
        "identifiers.py",
        "periods.py",
        "privacy.py",
        "provenance.py",
        "quality.py",
        "recommendations.py",
        "serialization.py",
        "values.py",
    }
    assert {path.name for path in CORE_FILES} == expected
