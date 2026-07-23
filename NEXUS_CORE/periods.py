"""Pure temporal models with no legal inference."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class PeriodPrecision(str, Enum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class PeriodStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class Period:
    start_date: date
    end_date: date | None = None
    precision: PeriodPrecision = PeriodPrecision.DAY

    def __post_init__(self) -> None:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("period end cannot precede start")

    @property
    def status(self) -> PeriodStatus:
        return PeriodStatus.OPEN if self.end_date is None else PeriodStatus.CLOSED

    def overlaps(self, other: "Period") -> bool:
        self_end = self.end_date or date.max
        other_end = other.end_date or date.max
        return self.start_date <= other_end and other.start_date <= self_end

    def contains(self, other: "Period") -> bool:
        self_end = self.end_date or date.max
        other_end = other.end_date or date.max
        return self.start_date <= other.start_date and self_end >= other_end
