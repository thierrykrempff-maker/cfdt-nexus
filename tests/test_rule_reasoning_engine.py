"""Architecture-only tests for Retirement Rule Reasoning LOT 5."""

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import (
    CareerEvidenceItem,
    EvidenceAuthorityLevel,
    EvidenceBundle,
    EvidenceConfidenceLevel,
    EvidenceId,
    EvidenceReference,
    EvidenceSourceType,
    EvidenceStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import CareerEvent, CareerEventType, CareerTimeline, EvidenceLevel
from RETIREMENT_PENIBILITY_ENGINE.document_knowledge_models import (
    DocumentPeriod,
    DocumentValidity,
    DocumentVersion,
    KnowledgeContext,
    KnowledgeRequest,
)
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_contract import (
    RULE_REASONING_SAFETY_CONTRACT,
    RetirementRuleReasoningPort,
)
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_engine import (
    RetirementRuleReasoningEngine,
)
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_models import (
    ConditionEvaluationState,
    ConditionOperator,
    GenericSchemeType,
    ReasoningFact,
    ReasoningFactStatus,
    ReasoningReport,
    ReasoningReportView,
    ReasoningRequest,
    ReasoningRule,
    RuleCondition,
    RuleConditionType,
)
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_policy import RULE_REASONING_POLICY
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_protocol import RULE_REASONING_PROTOCOL


def empty_context(*facts: ReasoningFact, evidence: tuple[CareerEvidenceItem, ...] = ()):
    timeline = CareerTimeline("timeline-1", "synthetic-case")
    bundle = EvidenceBundle("bundle-1", evidence=evidence)
    request = ReasoningRequest("reasoning-request-1", "Synthetic employee question")
    knowledge = KnowledgeContext(
        "knowledge-1",
        timeline.timeline_id,
        (),
        bundle.bundle_id,
        tuple(str(item.reference.evidence_id) for item in evidence),
        request.question,
        KnowledgeRequest("knowledge-request-1"),
    )
    return RetirementRuleReasoningEngine().create_reasoning_context(
        "context-1", request, timeline, bundle, knowledge, facts
    )


def condition(
    condition_id: str = "condition-1",
    condition_type: RuleConditionType = RuleConditionType.INEOS_SENIORITY,
    operator: ConditionOperator = ConditionOperator.GREATER_OR_EQUAL,
    fact_key: str = "declared_seniority",
    expected=20,
) -> RuleCondition:
    return RuleCondition(
        condition_id, condition_type, operator, fact_key, expected, "synthetic-rule-source"
    )


def rule(
    *conditions: RuleCondition,
    collective: bool = False,
    official: bool = False,
    version: DocumentVersion | None = None,
) -> ReasoningRule:
    return ReasoningRule(
        "rule-1",
        "Synthetic rule",
        GenericSchemeType.INEOS_END_OF_CAREER_MEASURE,
        conditions or (condition(),),
        "synthetic-rule-source",
        document_version=version,
        collective_rule=collective,
        official_validation_required=official,
    )


def supplied_evidence(source_type: EvidenceSourceType) -> CareerEvidenceItem:
    return CareerEvidenceItem(
        EvidenceReference(
            EvidenceId("evidence-1"), source_type, "Synthetic reference",
            "opaque-reference", "synthetic-evidence-source",
        ),
        EvidenceAuthorityLevel.DECLARATIVE_ONLY
        if source_type is EvidenceSourceType.EMPLOYEE_DECLARATION
        else EvidenceAuthorityLevel.CORROBORATING,
        EvidenceConfidenceLevel.UNKNOWN,
        EvidenceStatus.PROVIDED,
    )


def test_imports_contract_and_public_methods() -> None:
    contract = RULE_REASONING_SAFETY_CONTRACT
    assert contract.status == "ARCHITECTURE_ONLY"
    assert contract.enabled is False
    assert contract.network_allowed is False
    assert contract.document_access_allowed is False
    assert contract.retirement_calculation_allowed is False
    expected = {
        "create_reasoning_context", "register_rule", "evaluate_rule", "evaluate_rules",
        "identify_applicable_schemes", "identify_missing_information", "identify_conflicts",
        "generate_reasoning_report", "explain_reasoning",
    }
    assert expected <= set(RetirementRuleReasoningPort.__dict__)


def test_create_empty_context_and_register_rule_immutably() -> None:
    engine = RetirementRuleReasoningEngine()
    context = empty_context()
    registered = engine.register_rule(context, rule())
    assert context.rules == ()
    assert registered.rules[0].rule_id == "rule-1"
    with pytest.raises(FrozenInstanceError):
        registered.context_id = "changed"


def test_simple_condition_satisfied() -> None:
    context = empty_context(ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "synthetic"))
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(context, rule())
    assert evaluation.state is ConditionEvaluationState.SATISFIED
    assert evaluation.conditions[0].state is ConditionEvaluationState.SATISFIED


def test_simple_condition_not_satisfied() -> None:
    context = empty_context(ReasoningFact("declared_seniority", 10, ReasoningFactStatus.KNOWN, "synthetic"))
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(context, rule())
    assert evaluation.state is ConditionEvaluationState.NOT_SATISFIED


def test_unknown_value_is_never_invented() -> None:
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(empty_context(), rule())
    assert evaluation.state is ConditionEvaluationState.UNKNOWN
    assert evaluation.conditions[0].observed_value is None


def test_conflicted_fact_remains_conflicted() -> None:
    context = empty_context(ReasoningFact("declared_seniority", 20, ReasoningFactStatus.CONFLICTED, "two synthetic sources"))
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(context, rule())
    assert evaluation.state is ConditionEvaluationState.CONFLICTED


def test_mixed_known_and_unknown_conditions_are_partial() -> None:
    context = empty_context(ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "synthetic"))
    second = condition("condition-2", RuleConditionType.INEOS_POSITION, ConditionOperator.EQUALS, "position", "synthetic-position")
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(context, rule(condition(), second))
    assert evaluation.state is ConditionEvaluationState.PARTIALLY_SATISFIED


def test_missing_document_is_explicit() -> None:
    required = condition(
        "document-condition", RuleConditionType.DOCUMENT_REQUIRED,
        ConditionOperator.PRESENT, "required_document", True,
    )
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(empty_context(), rule(required))
    assert evaluation.state is ConditionEvaluationState.REQUIRES_DOCUMENT
    outcome = RetirementRuleReasoningEngine().evaluate_rules(
        RetirementRuleReasoningEngine().register_rule(empty_context(), rule(required))
    )
    assert outcome.gaps[0].required_document == "document-condition"


def test_official_notification_requirement_is_explicit() -> None:
    required = condition(
        "official-condition", RuleConditionType.OFFICIAL_NOTIFICATION_REQUIRED,
        ConditionOperator.PRESENT, "official_notification", True,
    )
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(empty_context(), rule(required))
    assert evaluation.state is ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION


def test_collective_rule_alone_is_not_individual_confirmation() -> None:
    context = empty_context(ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "synthetic"))
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(context, rule(collective=True))
    assert evaluation.state is ConditionEvaluationState.PARTIALLY_SATISFIED


def test_employee_declaration_alone_requires_validation() -> None:
    context = empty_context(
        ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "employee declaration", declarative=True),
        evidence=(supplied_evidence(EvidenceSourceType.EMPLOYEE_DECLARATION),),
    )
    evaluation = RetirementRuleReasoningEngine().evaluate_rule(context, rule())
    assert evaluation.state is ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION


def test_career_event_presence_is_checked_without_duration_calculation() -> None:
    context = empty_context()
    event = CareerEvent(
        "event-1", "2020-01-01", "2020-12-31", CareerEventType.NIGHT_WORK,
        "Synthetic night work", "synthetic", EvidenceLevel.B,
    )
    context = context.__class__(
        context.context_id,
        context.request,
        CareerTimeline("timeline-1", events=(event,)),
        context.evidence_bundle,
        context.knowledge_context,
        context.facts,
        context.rules,
    )
    present = condition(
        "event-condition", RuleConditionType.OTHER_DECLARED_FACT,
        ConditionOperator.EVENT_PRESENT, "event_type", "NIGHT_WORK",
    )
    assert RetirementRuleReasoningEngine().evaluate_rule(context, rule(present)).state is ConditionEvaluationState.SATISFIED


def test_date_in_declared_period_is_deterministic() -> None:
    context = empty_context(ReasoningFact("applicable_date", "2021-06-01", ReasoningFactStatus.KNOWN, "synthetic"))
    dated = condition(
        "date-condition", RuleConditionType.AGREEMENT_VALIDITY,
        ConditionOperator.IN_PERIOD, "applicable_date", ("2020-01-01", "2022-12-31"),
    )
    assert RetirementRuleReasoningEngine().evaluate_rule(context, rule(dated)).state is ConditionEvaluationState.SATISFIED


def test_valid_document_version_is_retained_and_repealed_is_excluded() -> None:
    active = DocumentVersion(
        "version-active", "document-1", "Synthetic active version",
        DocumentPeriod("2020-01-01", None), DocumentValidity.ACTIVE,
        provenance="synthetic-document-source",
    )
    repealed = DocumentVersion(
        "version-repealed", "document-1", "Synthetic repealed version",
        DocumentPeriod("2020-01-01", None), DocumentValidity.REPEALED,
        provenance="synthetic-document-source",
    )
    context = empty_context(ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "synthetic"))
    engine = RetirementRuleReasoningEngine()
    assert engine.evaluate_rule(context, rule(version=active)).state is ConditionEvaluationState.SATISFIED
    assert engine.evaluate_rule(context, rule(version=repealed)).state is ConditionEvaluationState.NOT_APPLICABLE


def test_outcome_preserves_provenance_structured_trace_and_scheme() -> None:
    engine = RetirementRuleReasoningEngine()
    context = empty_context(ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "synthetic-fact-source"))
    context = engine.register_rule(context, rule())
    outcome = engine.evaluate_rules(context)
    assert outcome.schemes[0].scheme is GenericSchemeType.INEOS_END_OF_CAREER_MEASURE
    assert outcome.trace[0].input_used == "declared_seniority"
    assert outcome.trace[0].provenance == "synthetic-fact-source"
    assert engine.explain_reasoning(outcome) is outcome.trace


def test_employee_report_is_non_decisional_and_hides_technical_trace() -> None:
    engine = RetirementRuleReasoningEngine()
    context = engine.register_rule(
        empty_context(ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, "synthetic")),
        rule(official=True),
    )
    report = engine.generate_reasoning_report(context, engine.evaluate_rules(context), ReasoningReportView.EMPLOYEE_VIEW)
    assert report.schemes_to_examine
    assert report.official_validation_required is True
    assert report.trace == ()
    assert report.examined_rules == ()
    assert any("not an administrative decision" in warning for warning in report.warnings)


def test_expert_report_is_sourced_but_redacts_secrets_and_local_paths() -> None:
    unsafe_evidence = CareerEvidenceItem(
        EvidenceReference(
            EvidenceId("evidence-1"), EvidenceSourceType.PAYSLIP, "Synthetic",
            r"C:\private\secret.pdf", "token=synthetic-secret",
        ),
        EvidenceAuthorityLevel.CORROBORATING,
        EvidenceConfidenceLevel.UNKNOWN,
        EvidenceStatus.PROVIDED,
    )
    engine = RetirementRuleReasoningEngine()
    context = empty_context(
        ReasoningFact("declared_seniority", 21, ReasoningFactStatus.KNOWN, r"C:\private\fact.json"),
        evidence=(unsafe_evidence,),
    )
    context = engine.register_rule(context, rule())
    report = engine.generate_reasoning_report(context, engine.evaluate_rules(context), ReasoningReportView.EXPERT_VIEW)
    rendered = repr(report)
    assert report.examined_rules == ("Synthetic rule",)
    assert report.trace
    assert "C:\\private" not in rendered
    assert "token=" not in rendered
    assert "[REDACTED]" in rendered


def test_report_has_no_retirement_date_amount_or_c2p_result_fields() -> None:
    names = {item.name for item in fields(ReasoningReport)}
    assert "retirement_date" not in names
    assert "pension_amount" not in names
    assert "quarters" not in names
    assert "c2p_points" not in names


def test_condition_and_scheme_catalogs_are_complete() -> None:
    assert len(RuleConditionType) == 21
    assert {item.value for item in ConditionEvaluationState} == {
        "SATISFIED", "NOT_SATISFIED", "UNKNOWN", "PARTIALLY_SATISFIED",
        "CONFLICTED", "NOT_APPLICABLE", "REQUIRES_DOCUMENT",
        "REQUIRES_OFFICIAL_VALIDATION",
    }
    assert len(GenericSchemeType) == 14


def test_policy_and_protocol_are_complete_and_declarative() -> None:
    assert len(RULE_REASONING_POLICY) == 14
    assert tuple(step.ordinal for step in RULE_REASONING_PROTOCOL) == tuple(range(1, 19))
    assert RULE_REASONING_PROTOCOL[-1].step_id == "produce_expert_view"


def test_lot_has_no_network_document_ai_or_connector_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    paths = tuple(root.glob("rule_reasoning_*.py")) + (root / "rule_condition_evaluator.py",)
    forbidden = {
        "aiohttp", "bs4", "html.parser", "http.client", "openai", "pypdf",
        "requests", "scrapy", "socket", "ssl", "urllib", "urllib.request",
        "xml.etree.ElementTree",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert forbidden.isdisjoint(imports), path.name
        source = path.read_text(encoding="utf-8")
        assert "automation.official_knowledge.connectors" not in source
        assert "urlopen(" not in source
        assert "open(" not in source
