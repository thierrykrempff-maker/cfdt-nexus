"""Separate, deterministic normalization of injected career metadata."""

from __future__ import annotations

from dataclasses import fields
from datetime import date
import re

from .career_import_models import ImportBatch, ImportNormalization, ImportedCareerRecord


class CareerImportNormalizer:
    """Produce normalized projections without mutating original records."""

    def normalize(self, batch: ImportBatch) -> tuple[ImportNormalization, ...]:
        return tuple(self._normalize_record(record) for record in batch.records)

    def _normalize_record(self, record) -> ImportNormalization:
        if isinstance(record, ImportedCareerRecord):
            original = record.original_values
        else:
            original = tuple(
                (field.name, getattr(record, field.name))
                for field in fields(record)
                if field.name not in {"record_id", "provenance"}
                and isinstance(getattr(record, field.name), (str, type(None)))
            )
        normalized: list[tuple[str, str | None]] = []
        transformations: list[str] = []
        for key, value in original:
            updated = self._normalize_value(key, value)
            normalized.append((key, updated))
            if updated != value:
                transformations.append(f"{key}: normalized")
        return ImportNormalization(
            record.record_id,
            original,
            tuple(normalized),
            tuple(transformations),
            record.provenance,
        )

    @staticmethod
    def _normalize_value(key: str, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if key.endswith("_date"):
            try:
                return date.fromisoformat(stripped).isoformat()
            except ValueError:
                return stripped
        if key in {"employer", "job_position"}:
            return " ".join(part.capitalize() for part in re.split(r"\s+", stripped) if part)
        if key in {"classification", "coefficient"}:
            return stripped.upper()
        if key in {"schedule", "work_schedule"}:
            return " ".join(stripped.split())
        if key in {"night_work", "five_shift", "part_time", "work_stoppage", "accident"}:
            return stripped.lower()
        return stripped
