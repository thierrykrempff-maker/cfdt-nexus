"""Isolated, synthetic-only tests for ARCH-01 common contracts."""

from __future__ import annotations

import ast
import importlib
import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from automation.contracts import (
    ConfidenceAssessment,
    ConfidenceDimension,
    ConfidenceLevel,
    ConfidentialityLevel,
    ConnectionStatus,
    ConsultationStatus,
    CriticalityLevel,
    ExpertReport,
    ExpertRequest,
    KnowledgeSource,
    MissingInformation,
    ReportStatus,
    RiskAssessment,
    SourceCategory,
    SourceEvidence,
    Statement,
    StatementKind,
)


NOW = datetime(2099, 1, 15, 10, 30, tzinfo=timezone.utc)


def statement(kind: StatementKind, suffix: str = "1") -> Statement:
    return Statement(f"STMT_{suffix}", "Élément entièrement synthétique.", kind)


def missing(suffix: str = "1") -> MissingInformation:
    return MissingInformation(
        f"MISS_{suffix}",
        "Bulletin synthétique absent.",
        "Nécessaire pour contrôler la rubrique.",
        CriticalityLevel.HIGH,
        "salarié",
        "Pouvez-vous fournir le bulletin de la période ?",
        True,
        "paie",
    )


def risk(level: CriticalityLevel = CriticalityLevel.MEDIUM, suffix: str = "1") -> RiskAssessment:
    return RiskAssessment(
        f"RISK_{suffix}",
        "financial",
        "Risque synthétique d'écart de rémunération.",
        level,
        0.4,
        "Écart de salaire à vérifier.",
        "court terme",
        supporting_evidence=("DECL_1",),
        mitigation_actions=("Rassembler les pièces.",),
        domain="paie",
    )


def evidence(status: ConsultationStatus = ConsultationStatus.SUCCEEDED) -> SourceEvidence:
    return SourceEvidence(
        "EVID_1",
        "SRC_1",
        "local_fixture",
        status,
        NOW if status in {ConsultationStatus.SUCCEEDED, ConsultationStatus.CACHE_HIT} else None,
        "synthetic://source/1" if status in {ConsultationStatus.SUCCEEDED, ConsultationStatus.CACHE_HIT} else None,
        "sha256:" + "a" * 64 if status in {ConsultationStatus.SUCCEEDED, ConsultationStatus.CACHE_HIT} else None,
        "synthetic_success" if status in {ConsultationStatus.SUCCEEDED, ConsultationStatus.CACHE_HIT} else None,
    )


def source(consulted: bool = False) -> KnowledgeSource:
    return KnowledgeSource(
        "SRC_1",
        "Source synthétique",
        "Organisme fictif",
        SourceCategory.INTERNAL,
        "synthetic_fixture",
        False,
        True,
        ConfidentialityLevel.INTERNAL,
        ConnectionStatus.PARTIAL,
        reference="synthetic://source/1",
        published_on=date(2099, 1, 1),
        effective_on=date(2099, 1, 1),
        consulted_at=NOW if consulted else None,
        retrieval_evidence_id="EVID_1" if consulted else None,
        domains=("paie",),
        version="1.0",
        freshness="synthetic",
    )


def request() -> ExpertRequest:
    return ExpertRequest(
        "REQ_1",
        "Des heures supplémentaires fictives sont-elles dues ?",
        "paie",
        context={"period": "2099-01", "synthetic_only": True},
        facts=(statement(StatementKind.ESTABLISHED_FACT, "FACT"),),
        declared_information=(statement(StatementKind.DECLARED_INFORMATION, "DECL"),),
        available_evidence_refs=("DOC_SYNTHETIC_1",),
        missing_information=(missing(),),
        metadata={"extension": {"legacy_key": "kept"}},
    )


def report() -> ExpertReport:
    return ExpertReport(
        "REPORT_1",
        "REQ_1",
        "synthetic_expert",
        findings=("La déclaration n'est pas corroborée.",),
        conclusions=("Impossible de conclure sans pièces.",),
        recommendations=("Rassembler les pièces avant analyse.",),
        proposed_actions=("Demander le bulletin.",),
        questions_to_ask=("Quelle période est concernée ?",),
        missing_information=(missing(),),
        risks=(risk(),),
        sources=(source(consulted=True),),
        source_evidence=(evidence(),),
        contradictions=("Aucune contradiction établie.",),
        assumptions=(statement(StatementKind.ASSUMPTION, "ASSUME"),),
        scenarios=(statement(StatementKind.SCENARIO, "SCENARIO"),),
        confidence_assessments=(
            ConfidenceAssessment(
                "CONF_COMPLETE",
                ConfidenceDimension.CASE_COMPLETENESS,
                ConfidenceLevel.VERY_LOW,
                0.1,
                "Pièces indispensables absentes.",
            ),
        ),
        warnings=("Données synthétiques uniquement.",),
        status=ReportStatus.PARTIAL,
        metadata={"legacy": {"preserved": True}},
    )


class CreationAndValidationTests(unittest.TestCase):
    def test_create_every_main_contract(self) -> None:
        values = (request(), report(), source(), evidence(), missing(), risk(), ConfidenceAssessment("CONF_1", ConfidenceDimension.SOURCE_RELIABILITY))
        self.assertTrue(all(value.to_dict() for value in values))

    def test_empty_request_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "request_id must be a non-empty string"):
            ExpertRequest(" ", "Question ?", "paie")

    def test_empty_question_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "question_text must be a non-empty string"):
            ExpertRequest("REQ", "", "paie")

    def test_empty_ids_are_rejected_across_contracts(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_id"):
            KnowledgeSource("", "Nom", "Org", SourceCategory.OFFICIAL, "api", True, False, ConfidentialityLevel.PUBLIC, ConnectionStatus.PARTIAL)
        with self.assertRaisesRegex(ValueError, "evidence_id"):
            SourceEvidence("", "SRC", "test", ConsultationStatus.NOT_ATTEMPTED)
        with self.assertRaisesRegex(ValueError, "risk_id"):
            RiskAssessment("", "financial", "Description", CriticalityLevel.LOW, None, "Impact", "court")

    def test_report_request_coherence(self) -> None:
        value = report()
        value.validate_for_request(request())
        with self.assertRaisesRegex(ValueError, "does not match"):
            value.validate_for_request(ExpertRequest("OTHER", "Question ?", "paie"))

    def test_established_facts_reject_assumptions(self) -> None:
        with self.assertRaisesRegex(ValueError, "facts may contain only"):
            ExpertRequest("REQ", "Question ?", "paie", facts=(statement(StatementKind.ASSUMPTION),))

    def test_established_facts_reject_assumed_intentions(self) -> None:
        with self.assertRaisesRegex(ValueError, "intentions are forbidden"):
            ExpertRequest("REQ", "Question ?", "paie", facts=(statement(StatementKind.ASSUMED_INTENTION),))

    def test_declarations_reject_established_facts(self) -> None:
        with self.assertRaisesRegex(ValueError, "declared_information may contain only"):
            ExpertRequest("REQ", "Question ?", "paie", declared_information=(statement(StatementKind.ESTABLISHED_FACT),))

    def test_report_assumptions_and_scenarios_stay_separate(self) -> None:
        with self.assertRaisesRegex(ValueError, "assumptions may contain only"):
            ExpertReport("REP", "REQ", "expert", assumptions=(statement(StatementKind.SCENARIO),))

    def test_successful_evidence_requires_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires occurred_at"):
            SourceEvidence("E", "S", "api", ConsultationStatus.SUCCEEDED, exact_reference="synthetic://x", access_result="ok")

    def test_successful_evidence_requires_reference(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires exact_reference"):
            SourceEvidence("E", "S", "api", ConsultationStatus.SUCCEEDED, occurred_at=NOW, access_result="ok")

    def test_successful_evidence_requires_timezone(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            SourceEvidence("E", "S", "api", ConsultationStatus.SUCCEEDED, occurred_at=datetime(2099, 1, 1), exact_reference="synthetic://x", access_result="ok")

    def test_failed_evidence_requires_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires an error"):
            SourceEvidence("E", "S", "api", ConsultationStatus.FAILED)

    def test_consulted_is_derived_and_cannot_be_forged(self) -> None:
        payload = evidence().to_dict()
        payload["consulted"] = False
        with self.assertRaisesRegex(ValueError, "derived"):
            SourceEvidence.from_dict(payload)

    def test_source_consultation_date_requires_evidence_link(self) -> None:
        with self.assertRaisesRegex(ValueError, "consulted_at requires"):
            KnowledgeSource("S", "N", "P", SourceCategory.INTERNAL, "doc", False, True, ConfidentialityLevel.INTERNAL, ConnectionStatus.PARTIAL, consulted_at=NOW)

    def test_report_rejects_orphan_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "included in the report"):
            ExpertReport("REP", "REQ", "expert", source_evidence=(evidence(),))

    def test_report_rejects_duplicate_confidence_dimensions(self) -> None:
        first = ConfidenceAssessment("C1", ConfidenceDimension.CASE_COMPLETENESS, ConfidenceLevel.LOW)
        second = ConfidenceAssessment("C2", ConfidenceDimension.CASE_COMPLETENESS, ConfidenceLevel.HIGH)
        with self.assertRaisesRegex(ValueError, "one assessment per dimension"):
            ExpertReport("REP", "REQ", "expert", confidence_assessments=(first, second))

    def test_critical_risk_requires_description_and_impact(self) -> None:
        with self.assertRaisesRegex(ValueError, "description"):
            RiskAssessment("R", "legal", "", CriticalityLevel.CRITICAL, 0.9, "Impact", "immédiat")
        with self.assertRaisesRegex(ValueError, "impact"):
            RiskAssessment("R", "legal", "Description", CriticalityLevel.CRITICAL, 0.9, "", "immédiat")

    def test_all_risk_levels_are_supported(self) -> None:
        self.assertEqual(set(CriticalityLevel), {item.level for item in (risk(level, str(index)) for index, level in enumerate(CriticalityLevel))})


class SerializationTests(unittest.TestCase):
    def test_round_trip_every_main_contract(self) -> None:
        values = (request(), report(), source(), evidence(), missing(), risk(), ConfidenceAssessment("CONF", ConfidenceDimension.LEGAL_SOLIDITY, ConfidenceLevel.HIGH, 0.8))
        for value in values:
            with self.subTest(contract=type(value).__name__):
                payload = value.to_dict()
                json.dumps(payload, ensure_ascii=False, sort_keys=True)
                self.assertEqual(type(value).from_dict(payload), value)

    def test_metadata_extensions_are_preserved(self) -> None:
        value = ExpertRequest("REQ", "Question ?", "paie", metadata={"unknown_extension": {"values": [1, 2, 3]}})
        self.assertEqual(value.to_dict()["metadata"]["unknown_extension"]["values"], [1, 2, 3])
        self.assertEqual(ExpertRequest.from_dict(value.to_dict()), value)

    def test_unknown_top_level_fields_are_rejected(self) -> None:
        payload = request().to_dict()
        payload["future_field"] = True
        with self.assertRaisesRegex(ValueError, "unknown field"):
            ExpertRequest.from_dict(payload)

    def test_non_json_metadata_is_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "JSON-compatible"):
            ExpertRequest("REQ", "Question ?", "paie", metadata={"bad": {1, 2}})

    def test_mutable_values_are_not_shared(self) -> None:
        raw_context = {"items": ["one"]}
        first = ExpertRequest("REQ_1", "Question ?", "paie", context=raw_context)
        second = ExpertRequest("REQ_2", "Question ?", "paie")
        raw_context["items"].append("two")
        self.assertEqual(first.to_dict()["context"]["items"], ["one"])
        self.assertEqual(second.to_dict()["context"], {})
        with self.assertRaises(TypeError):
            first.context["new"] = True  # type: ignore[index]

    def test_optional_dates_are_stable_iso_values(self) -> None:
        payload = source(consulted=True).to_dict()
        self.assertEqual(payload["published_on"], "2099-01-01")
        self.assertEqual(payload["consulted_at"], "2099-01-15T10:30:00+00:00")


class ConfidenceTests(unittest.TestCase):
    def test_all_dimensions_are_distinct(self) -> None:
        assessments = tuple(ConfidenceAssessment(f"CONF_{item.value}", item, ConfidenceLevel.LOW) for item in ConfidenceDimension)
        self.assertEqual({item.dimension for item in assessments}, set(ConfidenceDimension))
        self.assertEqual(len(assessments), 7)

    def test_all_canonical_levels_are_supported(self) -> None:
        self.assertEqual([item.value for item in ConfidenceLevel], ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"])

    def test_unknown_dimension_is_explicit_not_medium(self) -> None:
        value = ConfidenceAssessment("CONF", ConfidenceDimension.CASE_COMPLETENESS)
        self.assertFalse(value.known)
        self.assertIsNone(value.level)
        self.assertIsNone(value.to_dict()["level"])

    def test_unknown_confidence_cannot_have_score(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown"):
            ConfidenceAssessment("CONF", ConfidenceDimension.CASE_COMPLETENESS, score=0.5)

    def test_score_is_bounded(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            ConfidenceAssessment("CONF", ConfidenceDimension.QUESTION_RELEVANCE, ConfidenceLevel.HIGH, 1.1)


class IsolationAndCompatibilityTests(unittest.TestCase):
    def test_public_import_is_stable(self) -> None:
        package = importlib.import_module("automation.contracts")
        expected = {"ExpertRequest", "ExpertReport", "KnowledgeSource", "SourceEvidence", "MissingInformation", "RiskAssessment", "ConfidenceAssessment"}
        self.assertTrue(expected <= set(package.__all__))

    def test_package_has_no_domain_or_connector_dependency(self) -> None:
        package_dir = Path(__file__).resolve().parent
        forbidden = ("automation.experts", "automation.payroll", "automation.connector_platform", "automation.official_knowledge")
        allowed_roots = {"__future__", "dataclasses", "datetime", "enum", "json", "types", "typing"}
        for path in package_dir.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    modules = [node.module or ""]
                else:
                    continue
                self.assertFalse(any(module.startswith(forbidden) for module in modules), path.name)
                self.assertTrue(all(module.split(".")[0] in allowed_roots for module in modules), (path.name, modules))

    def test_source_syntax_is_python_310_compatible(self) -> None:
        package_dir = Path(__file__).resolve().parent
        for path in package_dir.glob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 10))

    def test_import_does_not_load_domain_packages(self) -> None:
        self.assertNotIn("automation.experts", sys.modules)
        self.assertNotIn("automation.payroll", sys.modules)
        self.assertNotIn("automation.connector_platform", sys.modules)


class SyntheticBusinessScenarioTests(unittest.TestCase):
    def test_unpaid_overtime_declaration_stays_unverified(self) -> None:
        declaration = Statement(
            "DECL_OVERTIME_1",
            "Le salarié fictif déclare des heures supplémentaires non payées.",
            StatementKind.DECLARED_INFORMATION,
        )
        bulletin = MissingInformation(
            "MISS_PAYSLIP",
            "Bulletin de paie de la période.",
            "Nécessaire pour vérifier les rubriques et montants.",
            CriticalityLevel.HIGH,
            "salarié",
            "Pouvez-vous fournir le bulletin fictif de la période ?",
            True,
            "paie",
        )
        time_record = MissingInformation(
            "MISS_TIME_RECORD",
            "Relevé horaire de la période.",
            "Nécessaire pour corroborer les heures déclarées.",
            CriticalityLevel.HIGH,
            "salarié",
            "Pouvez-vous fournir le relevé horaire fictif ?",
            True,
            "paie",
        )
        value = ExpertRequest(
            "REQ_OVERTIME_SYNTHETIC",
            "Des heures supplémentaires fictives semblent non payées : que vérifier ?",
            "paie",
            facts=(),
            declared_information=(declaration,),
            missing_information=(bulletin, time_record),
            metadata={"synthetic_only": True},
        )
        completeness = ConfidenceAssessment(
            "CONF_COMPLETENESS",
            ConfidenceDimension.CASE_COMPLETENESS,
            ConfidenceLevel.VERY_LOW,
            0.1,
            "Aucun bulletin ni relevé horaire n'est disponible.",
        )
        result = ExpertReport(
            "REPORT_OVERTIME_SYNTHETIC",
            value.request_id,
            "synthetic_payroll_contract_test",
            conclusions=("Aucun fait de non-paiement n'est établi.",),
            questions_to_ask=("Quelles dates et quels horaires sont déclarés ?",),
            missing_information=value.missing_information,
            risks=(risk(CriticalityLevel.MEDIUM, "OVERTIME"),),
            confidence_assessments=(completeness,),
            status=ReportStatus.PARTIAL,
            metadata={"synthetic_only": True},
        )
        result.validate_for_request(value)
        self.assertEqual(value.facts, ())
        self.assertEqual(value.declared_information[0].kind, StatementKind.DECLARED_INFORMATION)
        self.assertEqual(len(result.missing_information), 2)
        self.assertEqual(result.risks[0].level, CriticalityLevel.MEDIUM)
        self.assertTrue(result.questions_to_ask)
        self.assertEqual(result.confidence_assessments[0].level, ConfidenceLevel.VERY_LOW)


if __name__ == "__main__":
    unittest.main()
