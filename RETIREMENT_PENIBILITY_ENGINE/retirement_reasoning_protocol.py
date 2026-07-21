"""Fifteen-step retirement reasoning protocol with no calculation engine."""

from dataclasses import dataclass
from enum import Enum


class ReasoningStep(str, Enum):
    """Stable identifiers for the future deterministic reasoning sequence."""

    IDENTIFY_REQUEST = "identify_request"
    IDENTIFY_GENERATION = "identify_generation"
    IDENTIFY_REGIME = "identify_regime"
    IDENTIFY_KNOWN_PERIODS = "identify_known_periods"
    CLASSIFY_AVAILABLE_EVIDENCE = "classify_available_evidence"
    IDENTIFY_MISSING_PERIODS = "identify_missing_periods"
    IDENTIFY_NIGHT_WORK = "identify_night_work"
    IDENTIFY_FIVE_SHIFT_WORK = "identify_five_shift_work"
    IDENTIFY_EXPOSURES = "identify_exposures"
    IDENTIFY_C2P_INFORMATION = "identify_c2p_information"
    IDENTIFY_INEOS_AGREEMENTS = "identify_ineos_agreements"
    VERIFY_SOURCE_CONSISTENCY = "verify_source_consistency"
    DETERMINE_CALCULABILITY_AND_CONFIDENCE = "determine_calculability_and_confidence"
    PROPOSE_ACTIONS = "propose_actions"
    GENERATE_REPORT = "generate_report"


@dataclass(frozen=True)
class RetirementReasoningStep:
    """One protocol instruction; it describes controls but executes none."""

    ordinal: int
    step: ReasoningStep
    description: str
    blocking_when_missing: bool = False


REASONING_PROTOCOL = (
    RetirementReasoningStep(1, ReasoningStep.IDENTIFY_REQUEST, "Identify the employee question and requested outcome."),
    RetirementReasoningStep(2, ReasoningStep.IDENTIFY_GENERATION, "Identify the declared generation without deriving a retirement date."),
    RetirementReasoningStep(3, ReasoningStep.IDENTIFY_REGIME, "Identify every potentially relevant retirement regime."),
    RetirementReasoningStep(4, ReasoningStep.IDENTIFY_KNOWN_PERIODS, "List known career periods without computing duration or quarters."),
    RetirementReasoningStep(5, ReasoningStep.CLASSIFY_AVAILABLE_EVIDENCE, "Classify available evidence through the declared A-D matrix."),
    RetirementReasoningStep(6, ReasoningStep.IDENTIFY_MISSING_PERIODS, "Identify gaps and missing documentary periods.", True),
    RetirementReasoningStep(7, ReasoningStep.IDENTIFY_NIGHT_WORK, "Identify declared night-work periods and supporting references."),
    RetirementReasoningStep(8, ReasoningStep.IDENTIFY_FIVE_SHIFT_WORK, "Identify declared 5x8 periods and supporting references."),
    RetirementReasoningStep(9, ReasoningStep.IDENTIFY_EXPOSURES, "Identify declared occupational exposures without inferring eligibility."),
    RetirementReasoningStep(10, ReasoningStep.IDENTIFY_C2P_INFORMATION, "Identify declared C2P information and administrative evidence."),
    RetirementReasoningStep(11, ReasoningStep.IDENTIFY_INEOS_AGREEMENTS, "Identify potentially applicable INEOS provisions and versions."),
    RetirementReasoningStep(12, ReasoningStep.VERIFY_SOURCE_CONSISTENCY, "Record contradictions, scope issues and source effective dates."),
    RetirementReasoningStep(13, ReasoningStep.DETERMINE_CALCULABILITY_AND_CONFIDENCE, "Block calculation when data is insufficient and assign only a prudential confidence level.", True),
    RetirementReasoningStep(14, ReasoningStep.PROPOSE_ACTIONS, "Propose documents, corrections and competent organizations to contact."),
    RetirementReasoningStep(15, ReasoningStep.GENERATE_REPORT, "Generate a sourced report with evidence, gaps, warnings and no computed retirement date."),
)
