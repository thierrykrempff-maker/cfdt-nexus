"""Public façade coordinating the final assistant components."""

from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from .actions import ActionGenerator
from .contradictions import ContradictionResolver
from .critic import FinalCritic
from .models import (
    AssistantRequest,
    Confidence,
    FinalAssistantResponse,
    NormalizedEngineResult,
    PrivacyDecision,
    SourceItem,
    TechnicalTrace,
)
from .normalization import normalize_request
from .orchestration import EngineOrchestrator, EngineRunner
from .planning import AnalysisPlanner
from .privacy import PrivacyGate
from .questions import merge_questions
from .routing import DomainDetector
from .sources import merge_sources
from .synthesis import SynthesisEngine


class NexusFinalAssistant:
    def __init__(
        self,
        runners: Mapping[str, EngineRunner],
        *,
        max_engines: int = 4,
    ) -> None:
        self._detector = DomainDetector()
        self._planner = AnalysisPlanner(max_engines)
        self._orchestrator = EngineOrchestrator(runners, max_engines)
        self._conflicts = ContradictionResolver()
        self._synthesis = SynthesisEngine()
        self._actions = ActionGenerator()
        self._critic = FinalCritic()
        self._privacy = PrivacyGate()

    def analyze(self, request: AssistantRequest) -> FinalAssistantResponse:
        normalized = normalize_request(request)
        privacy = self._privacy.assess(normalized)
        if privacy.decision is PrivacyDecision.BLOCKED:
            matches = self._detector.detect(replace(normalized, question="Demande confidentielle"))
            plan = self._planner.plan(normalized, matches)
            return FinalAssistantResponse(
                normalized,
                plan,
                matches,
                (),
                (),
                (),
                (),
                {"limits": ("Restitution bloquée par le contrôle de confidentialité.",)},
                (),
                self._critic.review((), ""),
                privacy.decision,
                Confidence.LOW,
                TechnicalTrace(plan.execution_order, (), (), True, self._planner.max_engines),
                privacy.codes,
            )
        safe_request = replace(normalized, question=privacy.sanitized_question)
        matches = self._detector.detect(safe_request)
        plan = self._planner.plan(safe_request, matches)
        results, trace = self._orchestrator.execute(safe_request, plan)
        conflicts = self._conflicts.resolve(results)
        sources = merge_sources(tuple(source for result in results for source in result.sources))
        questions = merge_questions(results, tuple(fact.statement for fact in safe_request.facts))
        summary = self._synthesis.build(safe_request, plan, results, conflicts)
        actions = self._actions.generate(safe_request, plan, results)
        critic = self._critic.review(results, str(summary))
        confidence = self._confidence(results, conflicts, questions)
        response = FinalAssistantResponse(
            safe_request,
            plan,
            matches,
            results,
            conflicts,
            sources,
            questions,
            summary,
            actions,
            critic,
            privacy.decision,
            confidence,
            trace,
            privacy.codes,
        )
        if not self._privacy.public_output_is_safe(str(response.to_dict())):
            raise ValueError("PUBLIC_OUTPUT_PRIVACY_FAILED")
        return response

    @staticmethod
    def _confidence(
        results: tuple[NormalizedEngineResult, ...],
        conflicts: tuple[object, ...],
        questions: tuple[object, ...],
    ) -> Confidence:
        available = sum(1 for item in results if item.available)
        if available >= 2 and not conflicts and not questions:
            return Confidence.HIGH
        if available >= 1:
            return Confidence.MEDIUM
        return Confidence.LOW
