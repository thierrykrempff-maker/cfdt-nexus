"""Deterministic Potential Rights Engine with no entitlement attribution."""

from __future__ import annotations

from .career_evidence_models import EvidenceSourceType, EvidenceStatus
from .career_timeline_validator import CareerTimelineValidator
from .potential_rights_models import (
    CaseMaturity,
    CaseMaturityIndicator,
    CaseMaturityIndicatorState,
    CaseMaturityIndicatorType,
    MissingRequirement,
    OfficialValidation,
    PotentialRight,
    PotentialRightCategory,
    PotentialRightEvidence,
    PotentialRightGap,
    PotentialRightPriority,
    PotentialRightReason,
    PotentialRightRecommendation,
    PotentialRightsAnalysis,
    PotentialRightsContext,
    PotentialRightsReport,
    PotentialRightsReportView,
    PotentialRightStatus,
)
from .potential_rights_report import PotentialRightsReportBuilder
from .potential_rights_scoring import CaseMaturityScorer


_CATEGORY_MAP = {
    "LEGAL_RETIREMENT_AGE": PotentialRightCategory.LEGAL_RETIREMENT,
    "FULL_RATE_RETIREMENT": PotentialRightCategory.LEGAL_RETIREMENT,
    "LONG_CAREER": PotentialRightCategory.LONG_CAREER,
    "PROGRESSIVE_RETIREMENT": PotentialRightCategory.PROGRESSIVE_RETIREMENT,
    "INEOS_END_OF_CAREER_MEASURE": PotentialRightCategory.INEOS_END_OF_CAREER,
    "INEOS_RETIREMENT_INDEMNITY": PotentialRightCategory.RETIREMENT_INDEMNITY,
    "C2P_EARLY_RETIREMENT": PotentialRightCategory.C2P,
    "PERMANENT_INCAPACITY_RETIREMENT": PotentialRightCategory.ATMP,
    "ATMP_RECOGNITION": PotentialRightCategory.ATMP,
    "NIGHT_WORK_PREVENTION": PotentialRightCategory.NIGHT_WORK,
    "WORKSTATION_ADAPTATION": PotentialRightCategory.RECLASSIFICATION,
    "DISABILITY_OR_UNFITNESS_ROUTE": PotentialRightCategory.RECLASSIFICATION,
    "CAREER_CORRECTION": PotentialRightCategory.CAREER_CORRECTION,
    "OTHER_SCHEME": PotentialRightCategory.OTHER_SCHEME,
}


class PotentialRightsEngine:
    """Transform a reasoning report into cautious schemes and case maturity."""

    def __init__(
        self,
        scorer: CaseMaturityScorer | None = None,
        report_builder: PotentialRightsReportBuilder | None = None,
        timeline_validator: CareerTimelineValidator | None = None,
    ) -> None:
        self._scorer = scorer or CaseMaturityScorer()
        self._report_builder = report_builder or PotentialRightsReportBuilder()
        self._timeline_validator = timeline_validator or CareerTimelineValidator()

    def create_context(
        self,
        context_id,
        timeline,
        evidence_bundle,
        knowledge_context,
        reasoning_report,
    ) -> PotentialRightsContext:
        return PotentialRightsContext(
            context_id,
            timeline,
            evidence_bundle,
            knowledge_context,
            reasoning_report,
            timeline.synthetic_only and evidence_bundle.synthetic_only and knowledge_context.synthetic_only,
        )

    def identify_potential_rights(
        self, context: PotentialRightsContext
    ) -> tuple[PotentialRight, ...]:
        categories: list[PotentialRightCategory] = []
        for scheme in context.reasoning_report.schemes_to_examine:
            normalized = scheme.upper().replace("/", "_").replace(" ", "_")
            categories.append(_CATEGORY_MAP.get(normalized, PotentialRightCategory.OTHER_SCHEME))
        categories = list(dict.fromkeys(categories))
        evidence = tuple(
            PotentialRightEvidence(
                str(item.reference.evidence_id),
                item.reference.source_type.value,
                item.status.value,
                item.reference.provenance,
            )
            for item in context.evidence_bundle.evidence
        )
        gaps = tuple(
            PotentialRightGap(f"gap:{index}", description, description)
            for index, description in enumerate(context.reasoning_report.missing_documents, 1)
        )
        if context.reasoning_report.conflicts:
            status = PotentialRightStatus.CONFLICTED
        elif context.reasoning_report.official_validation_required:
            status = PotentialRightStatus.OFFICIAL_VALIDATION_REQUIRED
        elif gaps:
            status = PotentialRightStatus.INFORMATION_MISSING
        else:
            status = PotentialRightStatus.TO_EXAMINE
        return tuple(
            PotentialRight(
                potential_right_id=f"potential:{category.value.lower()}",
                category=category,
                status=status,
                priority=PotentialRightPriority.NORMAL,
                reasons=(
                    PotentialRightReason(
                        f"reason:{category.value.lower()}",
                        "Ce dispositif semble devoir être examiné au regard du rapport de raisonnement fourni.",
                        "RULE_REASONING_REPORT",
                    ),
                ),
                evidence=evidence,
                gaps=gaps,
                official_validation_ids=(f"validation:{category.value.lower()}",)
                if context.reasoning_report.official_validation_required
                else (),
            )
            for category in categories
        )

    def calculate_case_maturity(self, context: PotentialRightsContext) -> CaseMaturity:
        indicators = self._build_indicators(context)
        has_material = bool(
            context.evidence_bundle.evidence
            or context.reasoning_report.schemes_to_examine
            or context.reasoning_report.document_versions
            or context.reasoning_report.missing_documents
        )
        return self._scorer.score(indicators, has_material)

    def identify_missing_requirements(
        self, context: PotentialRightsContext
    ) -> tuple[MissingRequirement, ...]:
        return tuple(
            MissingRequirement(
                f"requirement:{index}",
                None,
                description,
                "RULE_REASONING_REPORT",
            )
            for index, description in enumerate(context.reasoning_report.missing_documents, 1)
        )

    def identify_official_validations(
        self, context: PotentialRightsContext
    ) -> tuple[OfficialValidation, ...]:
        if not context.reasoning_report.official_validation_required:
            return ()
        return (
            OfficialValidation(
                "official-validation-1",
                None,
                "COMPETENT_OFFICIAL_AUTHORITY",
                "Une validation officielle reste nécessaire avant toute conclusion sur un droit.",
            ),
        )

    def generate_recommendations(
        self,
        missing: tuple[MissingRequirement, ...],
        validations: tuple[OfficialValidation, ...],
    ) -> tuple[PotentialRightRecommendation, ...]:
        recommendations = tuple(
            PotentialRightRecommendation(
                f"recommendation:document:{index}",
                item.category,
                "Fournir ou faire vérifier la référence documentaire manquante.",
            )
            for index, item in enumerate(missing, 1)
        )
        if validations:
            recommendations += (
                PotentialRightRecommendation(
                    "recommendation:official-validation",
                    None,
                    "Demander une validation à l’organisme officiel compétent.",
                    validations[0].authority,
                ),
            )
        return recommendations or (
            PotentialRightRecommendation(
                "recommendation:review",
                None,
                "Faire examiner les informations disponibles par un expert qualifié.",
            ),
        )

    def analyze(self, context: PotentialRightsContext) -> PotentialRightsAnalysis:
        rights = self.identify_potential_rights(context)
        maturity = self.calculate_case_maturity(context)
        missing = self.identify_missing_requirements(context)
        validations = self.identify_official_validations(context)
        recommendations = self.generate_recommendations(missing, validations)
        return PotentialRightsAnalysis(rights, maturity, missing, validations, recommendations)

    def generate_report(
        self,
        context: PotentialRightsContext,
        analysis: PotentialRightsAnalysis,
        view: PotentialRightsReportView,
    ) -> PotentialRightsReport:
        return self._report_builder.build(context, analysis, view)

    def _build_indicators(
        self, context: PotentialRightsContext
    ) -> tuple[CaseMaturityIndicator, ...]:
        evidence = context.evidence_bundle.evidence
        report = context.reasoning_report
        official_types = {
            EvidenceSourceType.OFFICIAL_RETIREMENT_RECORD,
            EvidenceSourceType.CARSAT_NOTIFICATION,
            EvidenceSourceType.CNAV_NOTIFICATION,
            EvidenceSourceType.C2P_NOTIFICATION,
            EvidenceSourceType.SOCIAL_SECURITY_DOCUMENT,
        }
        contradictions = bool(report.conflicts) or any(
            item.status is EvidenceStatus.CONTRADICTED for item in evidence
        )
        timeline_valid = self._timeline_validator.validate(context.timeline).valid
        return (
            self._indicator(CaseMaturityIndicatorType.EVIDENCE_AVAILABLE, CaseMaturityIndicatorState.AVAILABLE if evidence else CaseMaturityIndicatorState.MISSING, "Evidence references are present." if evidence else "No evidence reference is present.", "CAREER_EVIDENCE"),
            self._indicator(CaseMaturityIndicatorType.CONTRADICTORY_EVIDENCE, CaseMaturityIndicatorState.CONFLICTED if contradictions else CaseMaturityIndicatorState.COHERENT, "Contradictions remain visible." if contradictions else "No contradiction is reported.", "CAREER_EVIDENCE_AND_REASONING"),
            self._indicator(CaseMaturityIndicatorType.OFFICIAL_DOCUMENTS, CaseMaturityIndicatorState.AVAILABLE if any(item.reference.source_type in official_types for item in evidence) else CaseMaturityIndicatorState.MISSING, "An official documentary reference is present." if any(item.reference.source_type in official_types for item in evidence) else "No official documentary reference is present.", "CAREER_EVIDENCE"),
            self._indicator(CaseMaturityIndicatorType.MISSING_DOCUMENTS, CaseMaturityIndicatorState.MISSING if report.missing_documents else CaseMaturityIndicatorState.COHERENT, "Missing documents are listed." if report.missing_documents else "No missing document is listed.", "RULE_REASONING_REPORT"),
            self._indicator(CaseMaturityIndicatorType.DECLARATIVE_EVIDENCE, CaseMaturityIndicatorState.AVAILABLE if any(item.reference.source_type is EvidenceSourceType.EMPLOYEE_DECLARATION for item in evidence) else CaseMaturityIndicatorState.NOT_APPLICABLE, "Declarative evidence is explicitly identified." if any(item.reference.source_type is EvidenceSourceType.EMPLOYEE_DECLARATION for item in evidence) else "No declarative evidence is supplied.", "CAREER_EVIDENCE"),
            self._indicator(CaseMaturityIndicatorType.DOCUMENT_VERSIONS, CaseMaturityIndicatorState.AVAILABLE if report.document_versions else CaseMaturityIndicatorState.MISSING, "Document versions are identified." if report.document_versions else "No document version is identified.", "DOCUMENT_KNOWLEDGE"),
            self._indicator(CaseMaturityIndicatorType.ADMINISTRATIVE_VALIDATION, CaseMaturityIndicatorState.REQUIRES_VALIDATION if report.official_validation_required else CaseMaturityIndicatorState.COHERENT, "Administrative validation remains necessary." if report.official_validation_required else "No outstanding administrative validation is listed.", "RULE_REASONING_REPORT"),
            self._indicator(CaseMaturityIndicatorType.TIMELINE_COHERENCE, CaseMaturityIndicatorState.COHERENT if timeline_valid else CaseMaturityIndicatorState.CONFLICTED, "The supplied timeline is structurally coherent." if timeline_valid else "The supplied timeline contains structural anomalies.", "CAREER_TIMELINE"),
            self._indicator(CaseMaturityIndicatorType.DOCUMENTARY_COHERENCE, CaseMaturityIndicatorState.COHERENT if not report.conflicts else CaseMaturityIndicatorState.CONFLICTED, "The supplied documentary context has no reported conflict." if not report.conflicts else "Documentary conflicts remain visible.", "DOCUMENT_KNOWLEDGE"),
        )

    @staticmethod
    def _indicator(indicator_type, state, explanation, provenance):
        return CaseMaturityIndicator(indicator_type, state, explanation, provenance)
