"""Immutable business contracts for Expert Paie V2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum


class PayrollPhase(str, Enum):
    DETECTION = "detection"
    CONTROL = "control"
    SIMULATION = "simulation"
    AUTHORIZED_CALCULATION = "authorized_calculation"
    CALCULATION_REFUSED = "calculation_refused"


class PayrollEventType(str, Enum):
    OVERTIME = "overtime"
    NIGHT_WORK = "night_work"
    SUNDAY_WORK = "sunday_work"
    PUBLIC_HOLIDAY = "public_holiday"
    SHIFT_WORK = "shift_work"
    SHIFT_PREMIUM = "shift_premium"
    ON_CALL = "on_call"
    ON_CALL_INTERVENTION = "on_call_intervention"
    ON_CALL_TRAVEL = "on_call_travel"
    COMPENSATORY_REST = "compensatory_rest"
    RECOVERY = "recovery"
    PAID_LEAVE = "paid_leave"
    RTT = "rtt"
    SICKNESS = "sickness"
    WORK_ACCIDENT = "work_accident"
    UNPAID_ABSENCE = "unpaid_absence"
    SALARY_MAINTENANCE = "salary_maintenance"
    IJSS = "ijss"
    SUBROGATION = "subrogation"
    PROVIDENT = "provident"
    THIRTEENTH_MONTH = "thirteenth_month"
    EVENT_PREMIUM = "event_premium"
    REGULARIZATION = "regularization"
    DEDUCTION = "deduction"
    COUNTER_CORRECTION = "counter_correction"
    NOT_MODELLED = "not_modelled"


class Unit(str, Enum):
    HOUR = "hour"
    DAY = "day"
    RATE = "rate"
    AMOUNT = "amount"
    COUNT = "count"


class RuleStatus(str, Enum):
    ACTIVE = "active"
    TO_VERIFY = "to_verify"
    INACTIVE = "inactive"
    DISPUTED = "disputed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class ComparisonStatus(str, Enum):
    MATCH = "match"
    APPARENT_DIFFERENCE = "apparent_difference"
    PROBABLE_ANOMALY = "probable_anomaly"
    POSSIBLE_ANOMALY = "possible_anomaly"
    INSUFFICIENT_DATA = "insufficient_data"
    NO_ANOMALY_DETECTED = "no_anomaly_detected"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class EvidencePriority(str, Enum):
    ESSENTIAL = "essential"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    PRIORITY = "priority"
    USEFUL = "useful"
    COMPLEMENTARY = "complementary"


@dataclass(frozen=True, slots=True)
class PayrollPeriod:
    start: str
    end: str
    payroll_month: str
    clearly_defined: bool = True


@dataclass(frozen=True, slots=True)
class SyntheticEmployee:
    employee_id: str
    work_regime: str
    synthetic: bool = True

    def __post_init__(self) -> None:
        if not self.synthetic:
            raise ValueError("Expert Paie V2 fixtures must be synthetic")


@dataclass(frozen=True, slots=True)
class PayrollValue:
    name: str
    value: Decimal | None
    unit: Unit
    source: str
    period: str | None = None
    certain: bool = True


@dataclass(frozen=True, slots=True)
class PayrollEvent:
    event_type: PayrollEventType
    date_or_period: str
    quantity: Decimal | None
    unit: Unit
    source: str
    expected_rubric: str | None = None
    modelled: bool = True


@dataclass(frozen=True, slots=True)
class KelioCounter:
    counter_code: str
    period: str
    quantity: Decimal | None
    unit: Unit
    source: str = "synthetic_kelio"


@dataclass(frozen=True, slots=True)
class NibelisRubric:
    rubric_code: str
    period: str
    quantity: Decimal | None
    amount: Decimal | None
    source: str = "synthetic_nibelis"


@dataclass(frozen=True, slots=True)
class PayrollRule:
    rule_id: str
    title: str
    status: RuleStatus
    domain: str
    event_types: tuple[PayrollEventType, ...]
    required_variables: tuple[str, ...]
    required_parameters: tuple[str, ...]
    source_layer: str
    source: str
    priority: int
    calculation_allowed: bool = False
    formula: str | None = None
    result_unit: Unit = Unit.AMOUNT


@dataclass(frozen=True, slots=True)
class RuleSelection:
    rule_id: str
    title: str
    selected: bool
    reasons: tuple[str, ...]
    exclusion_reasons: tuple[str, ...]
    calculation_allowed: bool
    source_rank: int


@dataclass(frozen=True, slots=True)
class CalculationRefusal:
    code: str
    reason: str
    missing_data: tuple[str, ...]
    requested_documents: tuple[str, ...]
    rule_id: str | None
    recommended_action: str


@dataclass(frozen=True, slots=True)
class PayrollComparison:
    comparison_type: str
    expected: str
    observed: str
    difference: str | None
    status: ComparisonStatus
    alternative_explanations: tuple[str, ...]
    confidence: ConfidenceLevel


@dataclass(frozen=True, slots=True)
class CalculationTrace:
    rule_id: str
    base: Decimal
    quantity: Decimal
    rate: Decimal
    formula: str
    steps: tuple[str, ...]
    result: Decimal
    unit: Unit
    rounding: str
    confidence: ConfidenceLevel
    warnings: tuple[str, ...]
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PayrollEvidence:
    name: str
    utility: str
    source: str
    priority: EvidencePriority
    confidentiality: str
    limitation: str
    demonstrates: str


@dataclass(frozen=True, slots=True)
class PayrollQuestion:
    priority: QuestionPriority
    wording: str
    purpose: str


@dataclass(frozen=True, slots=True)
class PayrollStrategy:
    level: int
    name: str
    objective: str
    urgency: str
    actor: str
    pieces: tuple[str, ...]
    advantages: tuple[str, ...]
    limitations: tuple[str, ...]
    risks: tuple[str, ...]
    expected_result: str
    next_step: str


@dataclass(frozen=True, slots=True)
class PayrollV2Input:
    question: str
    period: PayrollPeriod | None
    employee: SyntheticEmployee
    events: tuple[PayrollEvent, ...] = ()
    planning_values: tuple[PayrollValue, ...] = ()
    kelio_counters: tuple[KelioCounter, ...] = ()
    nibelis_rubrics: tuple[NibelisRubric, ...] = ()
    parameters: tuple[PayrollValue, ...] = ()
    rules: tuple[PayrollRule, ...] = ()
    available_documents: tuple[str, ...] = ()
    contradictory_data: bool = False
    confidentiality_validated: bool = True
    source_domain: str | None = None


@dataclass(frozen=True, slots=True)
class PayrollV2Analysis:
    phase: PayrollPhase
    events: tuple[PayrollEvent, ...]
    rule_selections: tuple[RuleSelection, ...]
    comparisons: tuple[PayrollComparison, ...]
    calculation: CalculationTrace | None
    refusals: tuple[CalculationRefusal, ...]
    alternative_explanations: tuple[str, ...]
    questions: tuple[PayrollQuestion, ...]
    evidence: tuple[PayrollEvidence, ...]
    strategies: tuple[PayrollStrategy, ...]
    employee_explanation: tuple[str, ...]
    expert_explanation: tuple[str, ...]
    articulation: tuple[str, ...]
    confidence: ConfidenceLevel
    scenario_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {"analysis_type": "expert_paie_v2_control", **_serialize(asdict(self))}


def _serialize(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
