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

    def merge(
        self, records: tuple[ReconstructionRecord, ...]
    ) -> tuple[ReconstructionMerge, tuple[ReconstructionConflict, ...]]:
        keys = tuple(dict.fromkeys(key for record in records for key, _ in record.values))
        merged = []
        alternatives = []
        conflicts = []
        provenance = tuple(dict.fromkeys(item for record in records for item in record.provenance))
        for key in keys:
            values = tuple(
                dict(record.values).get(key)
                for record in records
                if not self._unknown(dict(record.values).get(key))
            )
            unique = tuple(dict.fromkeys(values))
            if len(unique) <= 1:
                merged.append((key, unique[0] if unique else None))
            else:
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
        status = ReconstructionStatus.PARTIALLY_MERGED if conflicts else ReconstructionStatus.MERGED
        result = ReconstructionMerge(
            "merge:" + ":".join(record.record_id for record in records),
            tuple(record.record_id for record in records),
            tuple(merged),
            tuple(alternatives),
            provenance,
            status,
        )
        return result, tuple(conflicts)

    @staticmethod
    def _unknown(value):
        return value is None or (
            isinstance(value, ReconstructionDate)
            and value.precision is DatePrecision.UNKNOWN
        )
