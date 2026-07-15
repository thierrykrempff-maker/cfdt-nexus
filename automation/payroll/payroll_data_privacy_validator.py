#!/usr/bin/env python
"""Local privacy checks for CFDT Nexus payroll referentials.

The validator is intentionally deterministic and local-only. It detects
personal, payroll-sensitive and secret-looking values before they can enter
tracked payroll fixtures or referentials. Reports always mask detected values.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_TEXT_FILE_BYTES = 1_000_000
MASK_MIN_RATIO = 0.70

RISK_FORBIDDEN = "forbidden"
RISK_REVIEW = "review"
RISK_ALLOWED = "allowed"

STATUS_BLOCKED = "blocked"
STATUS_WARNING = "warning"
STATUS_OK = "ok"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "local-index",
}

TEXT_EXTENSIONS = {
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".ps1",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

RISKY_BINARY_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".ods", ".pdf", ".png", ".jpg", ".jpeg", ".zip"}
RISKY_FILENAME_TOKENS = {
    "bulletin": "payslip_file",
    "payslip": "payslip_file",
    "fiche_paie": "payslip_file",
    "export_kelio": "kelio_export",
    "export_nibelis": "nibelis_export",
    "salaires": "salary_export",
    "salaire": "salary_export",
    "matricules": "employee_identifier_export",
    "matricule": "employee_identifier_export",
}
SECRET_FILENAME_TOKENS = {
    ".env": "environment_secret_file",
    "secret": "secret_file",
    "secrets": "secret_file",
    "private_key": "private_key_file",
    "id_rsa": "private_key_file",
    "backup": "backup_file",
}

GENERIC_SYNTHETIC_MARKERS = {
    "exemple_synthetique",
    "synthetic_example",
    "synthetic_only",
    "fictif",
    "fictive",
    "fictitious",
    "demo",
    "invalid",
}
EXPLICIT_SAFE_MARKERS = {
    "exemple_synthetique",
    "synthetic_example",
    "synthetic_only=true",
}
INVALID_SAMPLE_MARKERS = {
    "invalide",
    "invalid",
    "documented_invalid",
    "exemple_invalide",
}

GENERIC_ALLOWED_NAMES = {
    "personne alpha",
    "personne beta",
    "salarie exemple",
    "salarié exemple",
    "employee example",
    "test user",
}

FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "email",
        re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE),
        "Remplacer par une adresse reservee example.com ou supprimer la donnee.",
    ),
    (
        "iban",
        re.compile(r"\b[A-Z]{2}\d{2}(?:[\s-]?[A-Z0-9]){11,30}\b", re.IGNORECASE),
        "Ne jamais stocker d'IBAN ou de coordonnees bancaires dans Git.",
    ),
    (
        "french_social_security_number",
        re.compile(r"\b[12][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{2}\b"),
        "Supprimer tout NIR ou numero de securite sociale.",
    ),
    (
        "phone_number",
        re.compile(r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b"),
        "Supprimer le numero ou utiliser un exemple explicitement synthetique non rattache a une personne.",
    ),
    (
        "employee_identifier",
        re.compile(
            r"\b(?:matricule|employee\s*id|numero\s*salari[ee]|num[eé]ro\s*salari[ée])\b\s*(?:[:#=]|n[°o]\s*)\s*[A-Z0-9][A-Z0-9-]{2,}",
            re.IGNORECASE,
        ),
        "Supprimer tout matricule ou identifiant salarie.",
    ),
    (
        "bic",
        re.compile(r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),
        "Ne jamais stocker de BIC ou reference bancaire dans Git.",
    ),
    (
        "technical_secret",
        re.compile(
            r"\b(?:api[_-]?key|secret|password|passwd|token|access[_-]?token)\b\s*[:=]\s*['\"]?([A-Za-z0-9_./+=:-]{8,})",
            re.IGNORECASE,
        ),
        "Supprimer le secret et utiliser une variable locale hors Git.",
    ),
    (
        "technical_secret",
        re.compile(r"\b(?:sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9_]{10,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"),
        "Supprimer le token et le regenerer si sa valeur etait reelle.",
    ),
    (
        "postal_address",
        re.compile(r"\b\d{1,4}\s+(?:rue|avenue|boulevard|impasse|chemin|route|allee|allée)\b", re.IGNORECASE),
        "Supprimer l'adresse postale ou la remplacer par un lieu generique.",
    ),
)

NOMINATIVE_FIELD_TOKENS = {
    "nom",
    "prenom",
    "prénom",
    "name",
    "employee_name",
    "salarie",
    "salarié",
    "collaborateur",
}
MATRICULE_FIELD_TOKENS = {"matricule", "employee_id", "numero_salarie", "numéro_salarié", "employee_number"}
BIRTH_DATE_FIELD_TOKENS = {"date_naissance", "birth_date", "dob", "date_de_naissance"}
BIRTH_PLACE_FIELD_TOKENS = {"lieu_naissance", "birth_place", "place_of_birth"}
TAX_FIELD_TOKENS = {"numero_fiscal", "tax_number", "tax_id", "taux_prelevement", "withholding_tax"}
MEDICAL_FIELD_TOKENS = {
    "diagnostic",
    "pathologie",
    "maladie",
    "medical",
    "médical",
    "sante",
    "santé",
    "arret_maladie",
    "arrêt_maladie",
    "work_stoppage",
}
SALARY_FIELD_TOKENS = {"salaire", "salary", "remuneration", "rémunération", "net_a_payer", "brut"}


@dataclass(frozen=True)
class PrivacyFinding:
    category: str
    path: str
    file_path: str | None
    masked_excerpt: str
    risk_level: str
    recommendation: str

    def as_dict(self) -> dict[str, str | None]:
        return asdict(self)


def normalize_key(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")


def is_synthetic_context(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in GENERIC_SYNTHETIC_MARKERS)


def is_explicit_safe_context(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in EXPLICIT_SAFE_MARKERS)


def is_documented_invalid_context(text: str) -> bool:
    lowered = text.lower()
    return is_explicit_safe_context(text) and any(marker in lowered for marker in INVALID_SAMPLE_MARKERS)


def is_allowed_email(value: str) -> bool:
    domain = value.rsplit("@", 1)[-1].lower()
    return domain == "example.com"


def mask_value(value: str) -> str:
    """Mask at least 70% of a detected value."""
    text = str(value)
    if not text:
        return ""
    if len(text) <= 3:
        return "*" * len(text)
    keep_total = max(0, int(len(text) * (1 - MASK_MIN_RATIO)))
    keep_total = min(keep_total, max(0, len(text) - 1))
    keep_start = min(2, keep_total)
    keep_end = max(0, keep_total - keep_start)
    if keep_end:
        return f"{text[:keep_start]}{'*' * (len(text) - keep_start - keep_end)}{text[-keep_end:]}"
    return f"{text[:keep_start]}{'*' * (len(text) - keep_start)}"


def masked_context(text: str, match_start: int, match_end: int) -> str:
    before = text[max(0, match_start - 12) : match_start]
    after = text[match_end : min(len(text), match_end + 12)]
    return f"{before}{mask_value(text[match_start:match_end])}{after}".strip()


def finding(
    *,
    category: str,
    path: str,
    file_path: str | None,
    value: str,
    risk_level: str,
    recommendation: str,
    context: str | None = None,
    start: int = 0,
    end: int | None = None,
) -> PrivacyFinding:
    source_context = context if context is not None else value
    if end is None:
        end = len(value)
    masked = masked_context(source_context, start, end) if context is not None else mask_value(value)
    return PrivacyFinding(
        category=category,
        path=path,
        file_path=str(file_path) if file_path else None,
        masked_excerpt=masked,
        risk_level=risk_level,
        recommendation=recommendation,
    )


def build_report(findings: Iterable[PrivacyFinding]) -> dict[str, Any]:
    values = list(findings)
    forbidden = [item for item in values if item.risk_level == RISK_FORBIDDEN]
    review = [item for item in values if item.risk_level == RISK_REVIEW]
    status = STATUS_OK
    if forbidden:
        status = STATUS_BLOCKED
    elif review:
        status = STATUS_WARNING
    return {
        "status": status,
        "findings_count": len(values),
        "blocked_count": len(forbidden),
        "warning_count": len(review),
        "findings": [item.as_dict() for item in values],
    }


def path_has_token(path: str, tokens: set[str]) -> bool:
    normalized = normalize_key(path)
    return any(token in normalized for token in tokens)


def is_generic_allowed_name(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in GENERIC_ALLOWED_NAMES or is_synthetic_context(value)


def scan_text(text: str, *, path: str = "$", file_path: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    findings: list[PrivacyFinding] = []
    context_text = text
    if context:
        context_text = f"{text} {json.dumps(context, ensure_ascii=False, sort_keys=True)}"

    for category, pattern, recommendation in FORBIDDEN_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            local_context = text[max(0, match.start() - 40) : min(len(text), match.end() + 40)]
            if category == "email" and is_allowed_email(value):
                continue
            if category == "phone_number" and is_explicit_safe_context(local_context):
                continue
            if category in {"iban", "french_social_security_number"} and is_documented_invalid_context(local_context):
                continue
            if category == "bic" and is_documented_invalid_context(local_context):
                continue
            findings.append(
                finding(
                    category=category,
                    path=path,
                    file_path=file_path,
                    value=value,
                    risk_level=RISK_FORBIDDEN,
                    recommendation=recommendation,
                    context=text,
                    start=match.start(),
                    end=match.end(),
                )
            )

    if path_has_token(path, MATRICULE_FIELD_TOKENS) and text.strip() and not is_synthetic_context(context_text):
        findings.append(
            finding(
                category="employee_identifier",
                path=path,
                file_path=file_path,
                value=text,
                risk_level=RISK_FORBIDDEN,
                recommendation="Supprimer le matricule ou utiliser un identifiant synthetique documente.",
            )
        )
    if path_has_token(path, BIRTH_DATE_FIELD_TOKENS) and re.search(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b", text):
        findings.append(
            finding(
                category="birth_date",
                path=path,
                file_path=file_path,
                value=text,
                risk_level=RISK_FORBIDDEN,
                recommendation="Supprimer toute date de naissance nominative.",
            )
        )
    if path_has_token(path, BIRTH_PLACE_FIELD_TOKENS) and text.strip() and not is_synthetic_context(context_text):
        findings.append(
            finding(
                category="birth_place",
                path=path,
                file_path=file_path,
                value=text,
                risk_level=RISK_FORBIDDEN,
                recommendation="Supprimer le lieu de naissance.",
            )
        )
    if path_has_token(path, TAX_FIELD_TOKENS) and text.strip() and not is_synthetic_context(context_text):
        findings.append(
            finding(
                category="tax_or_withholding_data",
                path=path,
                file_path=file_path,
                value=text,
                risk_level=RISK_FORBIDDEN,
                recommendation="Supprimer tout numero fiscal ou taux individualise.",
            )
        )
    return build_report(findings)


def object_has_nominative_context(value: dict[str, Any]) -> bool:
    for key, item in value.items():
        if path_has_token(str(key), NOMINATIVE_FIELD_TOKENS) and isinstance(item, str) and item.strip():
            if not is_generic_allowed_name(item):
                return True
            return True
    return False


def scan_object(value: Any, *, path: str = "$", file_path: str | None = None) -> dict[str, Any]:
    findings: list[PrivacyFinding] = []

    def visit(item: Any, current_path: str, parent: dict[str, Any] | None = None) -> None:
        if isinstance(item, dict):
            nominative_context = object_has_nominative_context(item)
            for key, child in item.items():
                child_path = f"{current_path}.{key}"
                normalized_key = normalize_key(str(key))
                if normalized_key in NOMINATIVE_FIELD_TOKENS and isinstance(child, str) and child.strip():
                    if not is_generic_allowed_name(child):
                        findings.append(
                            finding(
                                category="nominative_identity",
                                path=child_path,
                                file_path=file_path,
                                value=child,
                                risk_level=RISK_FORBIDDEN,
                                recommendation="Supprimer tout nom ou prenom reel d'une fixture.",
                            )
                        )
                if normalized_key in MEDICAL_FIELD_TOKENS and child not in (None, "", [], {}):
                    risk = RISK_FORBIDDEN if nominative_context else RISK_REVIEW
                    findings.append(
                        finding(
                            category="medical_or_work_stoppage_data",
                            path=child_path,
                            file_path=file_path,
                            value=str(child),
                            risk_level=risk,
                            recommendation="Ne jamais stocker de diagnostic, pathologie ou arret nominatif dans Git.",
                        )
                    )
                if normalized_key in SALARY_FIELD_TOKENS and child not in (None, "", [], {}) and nominative_context:
                    findings.append(
                        finding(
                            category="salary_tied_to_identity",
                            path=child_path,
                            file_path=file_path,
                            value=str(child),
                            risk_level=RISK_FORBIDDEN,
                            recommendation="Separer toute donnee de salaire de l'identite d'un salarie.",
                        )
                    )
                visit(child, child_path, item)
            return
        if isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{current_path}[{index}]", parent)
            return
        if isinstance(item, str):
            report = scan_text(item, path=current_path, file_path=file_path, context=parent)
            findings.extend(PrivacyFinding(**entry) for entry in report["findings"])

    visit(value, path)
    return build_report(findings)


def check_file_policy(path: Path | str) -> dict[str, Any]:
    file_path = Path(path)
    findings: list[PrivacyFinding] = []
    name = file_path.name.lower()
    suffix = file_path.suffix.lower()

    for token, category in SECRET_FILENAME_TOKENS.items():
        if token in name:
            findings.append(
                finding(
                    category=category,
                    path=str(file_path),
                    file_path=str(file_path),
                    value=file_path.name,
                    risk_level=RISK_FORBIDDEN,
                    recommendation="Ne pas versionner les secrets, sauvegardes ou fichiers d'environnement.",
                )
            )
            break
    for token, category in RISKY_FILENAME_TOKENS.items():
        if token in name:
            risk = RISK_FORBIDDEN if suffix in RISKY_BINARY_EXTENSIONS or suffix in {".csv", ".xlsx", ".xls"} else RISK_REVIEW
            findings.append(
                finding(
                    category=category,
                    path=str(file_path),
                    file_path=str(file_path),
                    value=file_path.name,
                    risk_level=risk,
                    recommendation="Verifier que ce fichier ne contient aucun export reel ou bulletin nominatif.",
                )
            )
            break
    return build_report(findings)


def scan_file(path: Path | str) -> dict[str, Any]:
    file_path = Path(path)
    findings: list[PrivacyFinding] = []
    findings.extend(PrivacyFinding(**entry) for entry in check_file_policy(file_path)["findings"])

    if not file_path.exists() or not file_path.is_file():
        return build_report(findings)
    if file_path.stat().st_size > MAX_TEXT_FILE_BYTES:
        findings.append(
            finding(
                category="large_file_not_scanned",
                path=str(file_path),
                file_path=str(file_path),
                value=file_path.name,
                risk_level=RISK_REVIEW,
                recommendation="Controle manuel requis pour les fichiers volumineux.",
            )
        )
        return build_report(findings)
    if file_path.suffix.lower() not in TEXT_EXTENSIONS:
        return build_report(findings)

    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = file_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            findings.append(
                finding(
                    category="unreadable_text_file",
                    path=str(file_path),
                    file_path=str(file_path),
                    value=file_path.name,
                    risk_level=RISK_REVIEW,
                    recommendation="Controle manuel requis pour ce fichier texte non lisible en UTF-8.",
                )
            )
            return build_report(findings)

    if file_path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            findings.extend(PrivacyFinding(**entry) for entry in scan_text(text, path="$", file_path=str(file_path))["findings"])
        else:
            findings.extend(PrivacyFinding(**entry) for entry in scan_object(data, path="$", file_path=str(file_path))["findings"])
    else:
        findings.extend(PrivacyFinding(**entry) for entry in scan_text(text, path="$", file_path=str(file_path))["findings"])
    return build_report(findings)


def should_skip_dir(path: Path) -> bool:
    return path.name in EXCLUDED_DIR_NAMES


def scan_directory(path: Path | str) -> dict[str, Any]:
    base_path = Path(path)
    findings: list[PrivacyFinding] = []
    if not base_path.exists():
        return build_report(findings)
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        dirs[:] = [dirname for dirname in dirs if not should_skip_dir(root_path / dirname)]
        for filename in files:
            report = scan_file(root_path / filename)
            findings.extend(PrivacyFinding(**entry) for entry in report["findings"])
    return build_report(findings)


def scan_paths(paths: Iterable[Path | str]) -> dict[str, Any]:
    findings: list[PrivacyFinding] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            report = scan_directory(path)
        else:
            report = scan_file(path)
        findings.extend(PrivacyFinding(**entry) for entry in report["findings"])
    return build_report(findings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan payroll files for private or sensitive data.")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    report = scan_paths(args.paths)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["status"] == STATUS_BLOCKED else 0


if __name__ == "__main__":
    raise SystemExit(main())
