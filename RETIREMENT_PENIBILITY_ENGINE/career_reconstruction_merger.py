"""Prudent merge of compatible structured reconstruction records."""

from __future__ import annotations

from .career_reconstruction_models import (
    DatePrecision,
    ReconstructionConflict,
    ReconstructionConflictType,
    ReconstructionDate,
    ReconstructionMerge,
    ReconstructionRecord,
    ReconstructionStatus,
)
from .document_resolution import DocumentResolutionStrategy
from .document_resolution_models import FactResolutionStatus


_CONFLICT_BY_FIELD = {
    "start_date": ReconstructionConflictType.DATE_CONFLICT,
    "end_date": ReconstructionConflictType.DATE_CONFLICT,
    "employer": ReconstructionConflictType.EMPLOYER_CONFLICT,
    "position": ReconstructionConflictType.POSITION_CONFLICT,
    "classification": ReconstructionConflictType.CLASSIFICATION_CONFLICT,
    "coefficient": ReconstructionConflictType.COEFFICIENT_CONFLICT,
    "schedule": ReconstructionConflictType.SCHEDULE_CONFLICT,
    "night_work": ReconstructionConflictType.NIGHT_WORK_CONFLICT,
    "five_shift": ReconstructionConflictType.FIVE_SHIFT_CONFLICT,
    "exposure_type": ReconstructionConflictType.EXPOSURE_CONFLICT,
}


class CareerReconstructionMerger:
    """Merge common values and preserve every incompatible alternative."""

    def __init__(self, resolution_strategy=None) -> None:
        self._resolution_strategy = resolution_strategy or DocumentResolutionStrategy()

    def merge(
        self, records: tuple[ReconstructionRecord, ...]
    ) -> tuple[ReconstructionMerge, tuple[ReconstructionConflict, ...]]:
        records = self._resolution_strategy.order(records)
        keys = tuple(dict.fromkeys(key for record in records for key, _ in record.values))
        merged = []
        alternatives = []
        conflicts = []
        resolutions = []
        provenance = tuple(dict.fromkeys(item for record in records for item in record.provenance))
        for key in keys:
            values = tuple(
                dict(record.values).get(key)
                for record in records
                if not self._unknown(dict(record.values).get(key))
            )
            unique = tuple(dict.fromkeys(values))
            resolution = self._resolution_strategy.resolve(key, records)
            resolutions.append(resolution)
            merged.append((key, resolution.selected_value))
            if len(unique) > 1:
                alternatives.append((key, unique))
                conflict_type = _CONFLICT_BY_FIELD.get(key, ReconstructionConflictType.PROVENANCE_CONFLICT)
                conflicts.append(
                    ReconstructionConflict(
                        f"conflict:{key}:" + ":".join(record.record_id for record in records),
                        conflict_type,
                        tuple(record.record_id for record in records),
                        ((key, unique),),
                        provenance,
                        f"Conflicting values retained for {key}.",
                    )
                )
        unresolved = {
            FactResolutionStatus.CONFLICT,
            FactResolutionStatus.UNSUPPORTED_FACT_TYPE,
        }
        if any(item.status in unresolved for item in resolutions):
            status = ReconstructionStatus.CONFLICTED
        elif conflicts:
            status = ReconstructionStatus.PARTIALLY_MERGED
        else:
            status = ReconstructionStatus.MERGED
        result = ReconstructionMerge(
            "merge:" + ":".join(record.record_id for record in records),
            tuple(record.record_id for record in records),
            tuple(merged),
            tuple(alternatives),
            provenance,
            status,
            tuple(record.record_id for record in records),
            tuple(resolutions),
        )
        return result, tuple(conflicts)

    @staticmethod
    def _unknown(value):
        return value is None or (
            isinstance(value, ReconstructionDate)
            and value.precision is DatePrecision.UNKNOWN
        )
