"""Context-aware detectors that never retain inspected values."""

from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Mapping

from .privacy_models import PrivacyCategory, PrivacyFinding, PrivacySeverity


_NIR_CANDIDATE = re.compile(r"(?<!\d)(?:[12][ .-]?)(?:\d[ .-]?){11}\d(?:[ .-]?\d{2})?(?!\d)")
_IBAN = re.compile(r"(?<![A-Z0-9])[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}(?![A-Z0-9])", re.IGNORECASE)
_RIB = re.compile(r"(?<!\w)\d{5}[ .-]+\d{5}[ .-]+[A-Z0-9]{11}[ .-]+\d{2}(?!\w)", re.IGNORECASE)
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?!\w)", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\d)(?:\+33[ .-]?[1-9]|0[1-9])(?:[ .-]?\d{2}){4}(?!\d)")
_ADDRESS = re.compile(r"\b\d{1,4}\s+(?:bis\s+|ter\s+)?(?:rue|avenue|boulevard|impasse|chemin|all[ée]e)\b", re.IGNORECASE)

_IDENTIFIER_FIELDS = {
    "employee_id",
    "matricule",
    "personnel_number",
    "kelio_id",
    "nibelis_id",
    "employee_number",
    "personnel_id",
}
_IDENTITY_FIELDS = {
    "first_name",
    "last_name",
    "full_name",
    "firstname",
    "lastname",
    "prenom",
    "nom",
    "employee_name",
}
_ADDRESS_FIELDS = {"address", "postal_address", "adresse", "adresse_postale"}
_SOURCE_FIELDS = {"origin", "source", "source_reference", "environment", "data_source"}
_REAL_SOURCE_MARKERS = (
    "real_data",
    "real-data",
    "production",
    "prod_export",
    "real_export",
    "real payslip",
    "real statement",
    "real document",
    "bulletin réel",
    "relevé réel",
    "export réel",
)
_SAFE_IDENTIFIER_PREFIXES = ("synthetic", "test", "fixture", "opaque", "anonymous", "anonymized", "anon")


class PrivacyDetector:
    """Walk supported immutable structures and emit value-free findings."""

    def inspect(self, value) -> tuple[PrivacyFinding, ...]:
        findings: list[PrivacyFinding] = []
        self._walk(value, "$", None, findings, set())
        return tuple(findings)

    def _walk(self, value, path, field_name, findings, active_ids) -> None:
        if value is None or isinstance(value, (bool, int, float, Enum)):
            return
        if isinstance(value, str):
            self._inspect_string(value, path, field_name or "", findings)
            return
        object_id = id(value)
        if object_id in active_ids:
            self._critical(findings, PrivacyCategory.INSPECTION, path, "PRIVACY_CYCLE_DETECTED", "Cyclic input cannot be inspected safely.")
            return
        active_ids.add(object_id)
        try:
            if is_dataclass(value) and not isinstance(value, type):
                for index, item in enumerate(fields(value)):
                    child = getattr(value, item.name)
                    child_path = f"{path}.field[{index}]"
                    if item.name == "synthetic_only" and child is not True:
                        self._critical(findings, PrivacyCategory.REAL_DOCUMENT, child_path, "PRIVACY_SYNTHETIC_REQUIRED", "Synthetic metadata is required.")
                    if item.name in {"provenance", "source", "source_reference"} and (child is None or child == ""):
                        self._critical(findings, PrivacyCategory.MISSING_PROVENANCE, child_path, "PRIVACY_PROVENANCE_REQUIRED", "Declared provenance is required.")
                    self._walk(child, child_path, item.name, findings, active_ids)
                return
            if isinstance(value, Mapping):
                for index, key in enumerate(sorted(value, key=lambda item: str(item))):
                    if not isinstance(key, str):
                        self._critical(findings, PrivacyCategory.INSPECTION, path, "PRIVACY_UNSUPPORTED_MAPPING_KEY", "Mapping keys must be text field names.")
                        continue
                    child = value[key]
                    child_path = f"{path}.entry[{index}]"
                    if key == "synthetic_only" and child is not True:
                        self._critical(findings, PrivacyCategory.REAL_DOCUMENT, child_path, "PRIVACY_SYNTHETIC_REQUIRED", "Synthetic metadata is required.")
                    if key in {"provenance", "source", "source_reference"} and (child is None or child == ""):
                        self._critical(findings, PrivacyCategory.MISSING_PROVENANCE, child_path, "PRIVACY_PROVENANCE_REQUIRED", "Declared provenance is required.")
                    self._walk(child, child_path, key, findings, active_ids)
                return
            if isinstance(value, (tuple, list)):
                for index, child in enumerate(value):
                    self._walk(child, f"{path}[{index}]", field_name, findings, active_ids)
                return
            if isinstance(value, (set, frozenset)):
                for index, child in enumerate(sorted(value, key=repr)):
                    self._walk(child, f"{path}[{index}]", field_name, findings, active_ids)
                return
            self._critical(findings, PrivacyCategory.INSPECTION, path, "PRIVACY_UNSUPPORTED_TYPE", "Input type cannot be inspected safely.")
        finally:
            active_ids.remove(object_id)

    def _inspect_string(self, value, path, field_name, findings) -> None:
        normalized_field = field_name.lower()
        lowered = value.lower()
        if _NIR_CANDIDATE.search(value):
            self._critical(findings, PrivacyCategory.NIR, path, "PRIVACY_NIR_DETECTED", "A French social-security identifier pattern is prohibited.")
        if _IBAN.search(value):
            self._critical(findings, PrivacyCategory.IBAN, path, "PRIVACY_IBAN_DETECTED", "A plausible bank account identifier is prohibited.")
        if _RIB.search(value):
            self._critical(findings, PrivacyCategory.RIB, path, "PRIVACY_RIB_DETECTED", "Structured bank coordinates are prohibited.")
        if _EMAIL.search(value):
            self._critical(findings, PrivacyCategory.PERSONAL_EMAIL, path, "PRIVACY_EMAIL_DETECTED", "Personal electronic mail data is prohibited.")
        if _PHONE.search(value):
            self._critical(findings, PrivacyCategory.PERSONAL_PHONE, path, "PRIVACY_PHONE_DETECTED", "Personal telephone data is prohibited.")
        if normalized_field in _ADDRESS_FIELDS and _ADDRESS.search(value):
            self._critical(findings, PrivacyCategory.POSTAL_ADDRESS, path, "PRIVACY_ADDRESS_DETECTED", "A personal postal address is prohibited.")
        if normalized_field in _IDENTITY_FIELDS and value and not self._is_synthetic(value):
            self._critical(findings, PrivacyCategory.DIRECT_IDENTITY, path, "PRIVACY_IDENTITY_DETECTED", "A direct personal identity is prohibited.")
        if normalized_field in _IDENTIFIER_FIELDS and value and not self._is_synthetic(value):
            self._critical(findings, PrivacyCategory.INTERNAL_IDENTIFIER, path, "PRIVACY_INTERNAL_ID_DETECTED", "A non-anonymized internal identifier is prohibited.")
        if normalized_field in _SOURCE_FIELDS and any(marker in lowered for marker in _REAL_SOURCE_MARKERS):
            self._critical(findings, PrivacyCategory.REAL_SOURCE, path, "PRIVACY_REAL_SOURCE_DETECTED", "Metadata declares a real or production source.")
        if normalized_field in {"path", "file_path", "document_path"} and self._looks_like_path(value):
            self._critical(findings, PrivacyCategory.REAL_DOCUMENT, path, "PRIVACY_REAL_PATH_DETECTED", "A local document path is prohibited.")
        if normalized_field in {"personal_note", "privacy_note"} and value:
            findings.append(
                PrivacyFinding(
                    PrivacyCategory.REVIEW_REQUIRED,
                    PrivacySeverity.WARNING,
                    path,
                    "PRIVACY_REVIEW_REQUIRED",
                    "A personal note field requires manual review.",
                    "Review metadata before continuing.",
                )
            )

    @staticmethod
    def _is_synthetic(value: str) -> bool:
        normalized = value.strip().lower().replace("_", "-")
        return normalized.startswith(_SAFE_IDENTIFIER_PREFIXES)

    @staticmethod
    def _looks_like_path(value: str) -> bool:
        return bool(re.match(r"^[A-Z]:[\\/]", value, re.IGNORECASE) or value.startswith(("/home/", "/Users/")))

    @staticmethod
    def _critical(findings, category, path, code, explanation) -> None:
        findings.append(
            PrivacyFinding(
                category,
                PrivacySeverity.CRITICAL,
                path,
                code,
                explanation,
                "Reject input and supply synthetic, anonymized metadata.",
            )
        )


__all__ = ("PrivacyDetector",)
