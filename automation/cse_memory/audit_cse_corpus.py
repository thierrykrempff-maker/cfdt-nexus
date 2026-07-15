"""Produce a metadata-only audit of the local CSE document corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
LEGACY_CONVERTER_EXTENSIONS = {".doc", ".xls", ".ppt"}
COMMON_AUXILIARY_EXTENSIONS = {".db", ".zip", ".7z", ".rar", ".rtf", ".csv", ".odt", ".ods", ".odp", ".msg", ".eml"}
YEAR_PATTERN = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    """Hash a file by blocks so large documents do not fill memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def detect_years(relative_path: str) -> list[str]:
    return sorted(set(YEAR_PATTERN.findall(relative_path)))


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def detect_family(relative_path: str) -> str:
    value = _normalized(relative_path).replace("_", " ").replace("-", " ")
    rules = (
        ("PV CSE", (r"\bpv\s+(?:du\s+)?cse\b", r"\bcse\s+pv\b")),
        ("CSSCT", (r"\bcssct\b",)),
        ("CHSCT", (r"\bchsct\b",)),
        ("NAO", (r"\bnao\b",)),
        ("consultations", (r"\bconsultation\w*\b", r"\bconsutation\w*\b")),
        ("expertises", (r"\bexpertise\w*\b", r"\bexpert\w*\b")),
        ("commissions", (r"\bcommission\w*\b",)),
        ("annexes", (r"\bannexe\w*\b",)),
        ("CE", (r"\bpv\s+(?:du\s+)?ce\b", r"\breunion\w*\s+(?:du\s+)?ce\b", r"\bce\b")),
    )
    for family, patterns in rules:
        if any(re.search(pattern, value) for pattern in patterns):
            return family
    return "autres"


def has_unusual_name(path: Path) -> bool:
    name = path.name
    return (
        name != name.strip()
        or name.startswith("~$")
        or any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Co", "Cn"} for char in name)
        or "\ufffd" in name
    )


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def audit_corpus(
    root: Path | str,
    *,
    hash_function: Callable[[Path], str] = sha256_file,
    long_path_threshold: int = 240,
) -> dict:
    """Inspect filenames and bytes without extracting or changing document content."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {root}")

    extension_counts: Counter[str] = Counter()
    year_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    hashes: dict[str, list[str]] = defaultdict(list)
    empty_files: list[str] = []
    unreadable_files: list[dict[str, str]] = []
    unusual_names: list[str] = []
    long_paths: list[str] = []
    supported_files: list[str] = []
    converter_files: list[str] = []
    walk_errors: list[dict[str, str]] = []
    total_size = 0
    total_files = 0
    total_directories = 0

    def on_walk_error(error: OSError) -> None:
        filename = Path(error.filename) if error.filename else root
        try:
            display = _relative(filename, root)
        except (ValueError, OSError):
            display = filename.name
        walk_errors.append({"path": display or ".", "error": type(error).__name__})

    for current, directories, files in os.walk(root, onerror=on_walk_error, followlinks=False):
        total_directories += len(directories)
        current_path = Path(current)
        for filename in files:
            path = current_path / filename
            relative = _relative(path, root)
            total_files += 1
            extension = path.suffix.casefold() or "[sans extension]"
            extension_counts[extension] += 1
            family_counts[detect_family(relative)] += 1
            for year in detect_years(relative):
                year_counts[year] += 1
            if has_unusual_name(path):
                unusual_names.append(relative)
            if len(relative) > long_path_threshold:
                long_paths.append(relative)
            if extension in SUPPORTED_EXTENSIONS:
                supported_files.append(relative)
            if extension in LEGACY_CONVERTER_EXTENSIONS or extension not in SUPPORTED_EXTENSIONS:
                converter_files.append(relative)

            try:
                size = path.stat().st_size
                total_size += size
                if size == 0:
                    empty_files.append(relative)
                hashes[hash_function(path)].append(relative)
            except (OSError, PermissionError) as error:
                unreadable_files.append({"path": relative, "error": type(error).__name__})

    unknown_extensions = sorted(
        extension for extension in extension_counts if extension not in SUPPORTED_EXTENSIONS
    )
    duplicates = [
        {"sha256": digest, "files": sorted(paths), "extra_copies": len(paths) - 1}
        for digest, paths in hashes.items()
        if len(paths) > 1
    ]
    duplicates.sort(key=lambda item: item["files"])
    converter_extensions = sorted(
        extension for extension in extension_counts
        if extension in LEGACY_CONVERTER_EXTENSIONS or extension not in SUPPORTED_EXTENSIONS
    )

    return {
        "audit_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "metadata and exact-byte hashes only; no content extraction",
        "total_files": total_files,
        "total_directories": total_directories,
        "total_size_bytes": total_size,
        "extensions": dict(sorted(extension_counts.items())),
        "unknown_extensions": unknown_extensions,
        "empty_file_count": len(empty_files),
        "empty_files": sorted(empty_files),
        "unreadable_file_count": len(unreadable_files) + len(walk_errors),
        "unreadable_files": unreadable_files + walk_errors,
        "unusual_name_count": len(unusual_names),
        "unusual_names": sorted(unusual_names),
        "long_path_threshold": long_path_threshold,
        "long_path_count": len(long_paths),
        "long_paths": sorted(long_paths),
        "duplicate_group_count": len(duplicates),
        "duplicate_extra_copy_count": sum(item["extra_copies"] for item in duplicates),
        "exact_duplicates": duplicates,
        "years": dict(sorted(year_counts.items())),
        "families": dict(sorted(family_counts.items())),
        "supported_file_count": len(supported_files),
        "supported_files": sorted(supported_files),
        "converter_required_extensions": converter_extensions,
        "converter_required_file_count": len(converter_files),
        "converter_required_files": sorted(converter_files),
    }


def _markdown_list(values: Iterable[str]) -> str:
    values = list(values)
    return "\n".join(f"- `{value}`" for value in values) if values else "- Aucun"


def render_markdown(report: dict) -> str:
    extensions = "\n".join(f"- `{key}` : {value}" for key, value in report["extensions"].items())
    years = "\n".join(f"- {key} : {value}" for key, value in report["years"].items()) or "- Aucune"
    families = "\n".join(f"- {key} : {value}" for key, value in report["families"].items())
    duplicates = []
    for group in report["exact_duplicates"]:
        duplicates.append(f"- SHA-256 `{group['sha256']}` ({len(group['files'])} fichiers)")
        duplicates.extend(f"  - `{path}`" for path in group["files"])
    unreadable = [f"{item['path']} ({item['error']})" for item in report["unreadable_files"]]
    return f"""# Audit local du corpus CSE

Audit de métadonnées et d'identité binaire uniquement. Aucun contenu documentaire n'est extrait.

## Synthèse

- Fichiers : {report['total_files']}
- Dossiers : {report['total_directories']}
- Taille : {report['total_size_bytes']} octets
- Fichiers vides : {report['empty_file_count']}
- Fichiers illisibles : {report['unreadable_file_count']}
- Groupes de doublons exacts : {report['duplicate_group_count']}
- Copies supplémentaires exactes : {report['duplicate_extra_copy_count']}

## Extensions

{extensions}

### Extensions inconnues

{_markdown_list(report['unknown_extensions'])}

### Formats nécessitant un convertisseur particulier

{_markdown_list(report['converter_required_extensions'])}

## Années probables

{years}

## Familles documentaires probables

{families}

## Fichiers vides

{_markdown_list(report['empty_files'])}

## Fichiers illisibles

{_markdown_list(unreadable)}

## Noms inhabituels

{_markdown_list(report['unusual_names'])}

## Chemins longs

{_markdown_list(report['long_paths'])}

## Doublons exacts

{chr(10).join(duplicates) if duplicates else '- Aucun'}

## Fichiers potentiellement pris en charge

{_markdown_list(report['supported_files'])}

## Fichiers nécessitant un convertisseur particulier

{_markdown_list(report['converter_required_files'])}
"""


def write_reports(report: dict, output_dir: Path | str) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cse_corpus_audit.json"
    markdown_path = output_dir / "cse_corpus_audit.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=project_root / "CCSEMEMORYENGINE" / "RAW_DOCUMENTS")
    parser.add_argument("--output", type=Path, default=project_root / "CCSEMEMORYENGINE" / "AUDIT")
    args = parser.parse_args()
    report = audit_corpus(args.corpus)
    json_path, markdown_path = write_reports(report, args.output)
    summary = {
        key: report[key]
        for key in (
            "total_files", "total_size_bytes", "extensions", "years",
            "duplicate_group_count", "empty_file_count", "unreadable_file_count",
            "unknown_extensions",
        )
    }
    summary["reports"] = [str(json_path), str(markdown_path)]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
