"""Single lazy adapter to the existing validated payroll Kelio catalog."""

from __future__ import annotations

from typing import Callable, Mapping

from automation.payroll import payroll_referential_validator

from .kelio_referential_models import (
    KelioCounterMetadata,
    KelioCounterResolution,
    KelioResolutionStatus,
)


class PayrollKelioReferentialLookup:
    """Resolve counters without exposing the catalog's physical location."""

    def __init__(
        self,
        catalog_loader: Callable[[], Mapping] | None = None,
        catalog_validator: Callable[[Mapping], Mapping] | None = None,
    ) -> None:
        self._catalog_loader = catalog_loader or (
            lambda: payroll_referential_validator.load_catalog("kelio")
        )
        self._catalog_validator = catalog_validator or (
            lambda catalog: payroll_referential_validator.validate_catalog(
                "kelio", catalog=dict(catalog)
            )
        )
        self._records: tuple[Mapping, ...] | None = None
        self._catalog_id = ""
        self._version = ""

    def resolve_counter(self, counter_id: str) -> KelioCounterResolution:
        if not isinstance(counter_id, str) or not counter_id.strip():
            return self._result(counter_id if isinstance(counter_id, str) else "", KelioResolutionStatus.UNKNOWN, "KELIO_COUNTER_ID_REQUIRED")
        try:
            records = self._load()
        except Exception:
            return self._result(counter_id, KelioResolutionStatus.LOOKUP_ERROR, "KELIO_REFERENTIAL_LOOKUP_ERROR")
        matches = tuple(
            item
            for item in records
            if counter_id in {item.get("counter_id"), item.get("counter_code")}
        )
        if not matches:
            return self._result(counter_id, KelioResolutionStatus.UNKNOWN, "KELIO_COUNTER_UNKNOWN")
        if len(matches) != 1:
            return self._result(counter_id, KelioResolutionStatus.LOOKUP_ERROR, "KELIO_COUNTER_AMBIGUOUS")
        record = matches[0]
        status, warnings, code = self._status(record)
        metadata = KelioCounterMetadata(
            referential_id=f"{self._catalog_id}:{self._version}",
            canonical_counter_id=str(record["counter_id"]),
            category=str(record["counter_type"]),
            source_type="KELIO_COUNTER_REFERENTIAL",
            resolution_status=status,
            evidence_kind=self._evidence_kind(str(record["counter_type"])),
            synthetic_only=record.get("synthetic_only") is True,
            calculation_allowed=record.get("calculation_allowed") is True,
            provenance=f"payroll-referential:{self._catalog_id}:{self._version}",
        )
        return KelioCounterResolution(counter_id, status, metadata, warnings, code)

    def is_known_counter(self, counter_id: str) -> bool:
        return self.resolve_counter(counter_id).usable

    def get_counter_metadata(self, counter_id: str) -> KelioCounterMetadata | None:
        resolution = self.resolve_counter(counter_id)
        return resolution.metadata if resolution.usable else None

    def list_supported_counter_ids(self) -> tuple[str, ...]:
        try:
            return tuple(
                sorted(
                    str(item["counter_id"])
                    for item in self._load()
                    if self._status(item)[0]
                    in {
                        KelioResolutionStatus.RESOLVED,
                        KelioResolutionStatus.RESOLVED_WITH_WARNINGS,
                    }
                )
            )
        except Exception:
            return ()

    def _load(self) -> tuple[Mapping, ...]:
        if self._records is not None:
            return self._records
        catalog = self._catalog_loader()
        if not isinstance(catalog, Mapping):
            raise ValueError("KELIO_REFERENTIAL_INVALID")
        report = self._catalog_validator(catalog)
        if report.get("valid") is not True:
            raise ValueError("KELIO_REFERENTIAL_INVALID")
        records = catalog.get("counters")
        if not isinstance(records, list):
            raise ValueError("KELIO_REFERENTIAL_INVALID")
        self._catalog_id = str(catalog.get("catalog_id") or "")
        self._version = str(catalog.get("version") or "")
        if not self._catalog_id or not self._version:
            raise ValueError("KELIO_REFERENTIAL_INVALID")
        self._records = tuple(item for item in records if isinstance(item, Mapping))
        if len(self._records) != len(records):
            raise ValueError("KELIO_REFERENTIAL_INVALID")
        return self._records

    @staticmethod
    def _status(record: Mapping):
        if record.get("synthetic_only") is not True:
            return KelioResolutionStatus.INCOMPATIBLE, (), "KELIO_COUNTER_NOT_SYNTHETIC"
        if record.get("calculation_allowed") is not False:
            return KelioResolutionStatus.INCOMPATIBLE, (), "KELIO_COUNTER_CALCULATION_PROHIBITED"
        if record.get("confidentiality") in {"confidential", "private"}:
            return KelioResolutionStatus.INCOMPATIBLE, (), "KELIO_COUNTER_CONFIDENTIAL"
        validation_status = record.get("validation_status")
        if validation_status == "rejected":
            return KelioResolutionStatus.INCOMPATIBLE, (), "KELIO_COUNTER_REJECTED"
        if validation_status in {"draft", "to_verify"}:
            return (
                KelioResolutionStatus.RESOLVED_WITH_WARNINGS,
                ("KELIO_COUNTER_REQUIRES_HUMAN_REVIEW",),
                "KELIO_COUNTER_RESOLVED_WITH_WARNINGS",
            )
        if validation_status not in {"synthetic_example", "human_validated"}:
            return KelioResolutionStatus.INCOMPATIBLE, (), "KELIO_COUNTER_STATUS_INCOMPATIBLE"
        return KelioResolutionStatus.RESOLVED, (), "KELIO_COUNTER_RESOLVED"

    @staticmethod
    def _evidence_kind(counter_type: str) -> str:
        return {
            "night_work": "WORK_SCHEDULE",
            "on_call": "WORK_SCHEDULE",
            "intervention": "WORK_SCHEDULE",
            "overtime": "WORKING_TIME",
            "pointing": "WORKING_TIME",
            "rest": "WORKING_TIME",
            "leave": "ABSENCE_METADATA",
            "absence": "ABSENCE_METADATA",
            "sickness": "ABSENCE_METADATA",
            "holiday": "WORKING_TIME",
            "sunday_work": "WORKING_TIME",
        }.get(counter_type, "CONTEXTUAL_METADATA")

    @staticmethod
    def _result(counter_id, status, code):
        return KelioCounterResolution(counter_id, status, code=code)


__all__ = ("PayrollKelioReferentialLookup",)
