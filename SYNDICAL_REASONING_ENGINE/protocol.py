"""Observable 18-step reasoning protocol."""

from __future__ import annotations

from enum import Enum


class ReasoningStep(str, Enum):
    NEUTRAL_REFORMULATION = "neutral_reformulation"
    SEPARATE_FACTS_AND_HYPOTHESES = "separate_facts_and_hypotheses"
    IDENTIFY_PERSONS_AND_BODIES = "identify_persons_and_bodies"
    DETECT_DOMAINS = "detect_domains"
    PROVISIONAL_QUALIFICATION = "provisional_qualification"
    RANK_SOURCES = "rank_sources"
    DETECT_SOURCE_CONTRADICTIONS = "detect_source_contradictions"
    IDENTIFY_EMPLOYEE_RIGHTS = "identify_employee_rights"
    IDENTIFY_EMPLOYER_OBLIGATIONS = "identify_employer_obligations"
    IDENTIFY_REPRESENTATIVE_ROLES = "identify_representative_roles"
    ASSESS_RISKS = "assess_risks"
    BUILD_ACTION_OPTIONS = "build_action_options"
    COMPARE_ACTION_OPTIONS = "compare_action_options"
    RECOMMEND_STRATEGY = "recommend_strategy"
    BUILD_CHRONOLOGICAL_PLAN = "build_chronological_plan"
    LIST_REQUIRED_EVIDENCE = "list_required_evidence"
    SIGNAL_UNCERTAINTIES = "signal_uncertainties"
    CAUTIOUS_CONCLUSION = "cautious_conclusion"


PROTOCOL_STEPS: tuple[ReasoningStep, ...] = tuple(ReasoningStep)
