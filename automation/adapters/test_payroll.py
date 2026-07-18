"""ARCH-02 tests for the isolated, retrocompatible payroll adapters."""

from __future__ import annotations

import ast
import copy
import importlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from automation.adapters.payroll import (
    ADAPTER_VERSION,
    expert_report_to_legacy_payroll,
    expert_report_to_legacy_payroll_result,
    expert_request_to_legacy_payroll,
    expert_request_to_legacy_payroll_request,
    expert_request_to_payroll_question,
    legacy_confidence_to_confidence_assessment,
    legacy_evidence_to_source_evidence,
    legacy_missing_information_to_contract,
    legacy_payroll_report_to_expert_report,
    legacy_payroll_request_to_expert_request,
    legacy_payroll_result_to_expert_report,
    legacy_risk_to_risk_assessment,
    legacy_source_to_knowledge_source,
    legacy_payroll_source_to_contracts,
    payroll_question_to_expert_request,
)
from automation.contracts import (
    ConfidenceAssessment,
    ConfidenceDimension,
    ConfidenceLevel,
    ConfidentialityLevel,
    CriticalityLevel,
    ExpertReport,
    ExpertRequest,
    ReportStatus,
    Statement,
    StatementKind,
)


def synthetic_request(subject: str = "heures_supplementaires") -> dict[str, object]:
    return {
        "case_id": f"SYN-{subject}",
        "query": f"Vérifier le scénario synthétique {subject}.",
        "domain": "paie",
        "context": {"subject": subject, "period": "2026-01"},
        "facts": [{"id": "FACT-SYN-1", "text": "Une rubrique synthétique figure sur le bulletin fictif."}],
        "declarations": [{"id": "DECL-SYN-1", "text": "La personne fictive déclare un écart."}],
        "hypotheses": ["Une rubrique pourrait être mal paramétrée."],
        "assumed_intentions": ["La direction pourrait vouloir régulariser."],
        "scenarios": ["Une régularisation pourrait intervenir le mois suivant."],
        "missing_information": [{
            "id": "MISS-SYN-1",
            "description": "Bulletin fictif détaillé",
            "reason": "Nécessaire au rapprochement.",
            "criticality": "HIGH",
            "blocking": True,
            "question": "Pouvez-vous fournir le bulletin fictif ?",
        }],
        "sources": [{"name": "Accord synthétique", "is_internal": True}],
        "custom_legacy_field": {"preserve": [1, 2, 3]},
    }


def synthetic_report(request_id: str = "SYN-REPORT-REQ") -> dict[str, object]:
    return {
        "report_id": "SYN-REPORT-1",
        "request_id": request_id,
        "active": True,
        "name": "Expert Paie V0",
        "objet_du_controle": "Contrôle synthétique d'une rubrique.",
        "elements_du_bulletin_concernes": ["Rubrique fictive"],
        "methode_de_controle": ["Rapprocher les pièces synthétiques."],
        "anomalies_potentielles": ["Un écart pourrait exister."],
        "donnees_necessaires_au_calcul": ["Bulletin fictif"],
        "sources_utilisees": ["Accord synthétique"],
        "niveau_de_confiance": "moyen",
        "limites": ["Aucun calcul automatique."],
        "custom_report_field": {"preserve": True},
    }


class RequestAdapterTests(unittest.TestCase):
    def test_minimal_request(self) -> None:
        adapted = legacy_payroll_request_to_expert_request({"query": "Question Paie synthétique"})
        self.assertEqual(adapted.question_text, "Question Paie synthétique")
        self.assertEqual(adapted.requested_domain, "paie")

    def test_complete_request(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertEqual(len(adapted.facts), 1)
        self.assertEqual(len(adapted.declared_information), 1)
        self.assertEqual(len(adapted.missing_information), 1)
        self.assertEqual(len(adapted.available_evidence_refs), 1)

    def test_invalid_request_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "question"):
            legacy_payroll_request_to_expert_request({"query": " "})

    def test_case_identifier_is_preserved(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertEqual(adapted.request_id, "SYN-heures_supplementaires")

    def test_question_is_preserved(self) -> None:
        legacy = synthetic_request()
        adapted = legacy_payroll_request_to_expert_request(legacy)
        self.assertEqual(adapted.question_text, legacy["query"])

    def test_facts_are_preserved_as_facts(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertIs(adapted.facts[0].kind, StatementKind.ESTABLISHED_FACT)

    def test_declarations_are_not_promoted_to_facts(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertFalse(any(item.text == adapted.declared_information[0].text for item in adapted.facts))
        self.assertIs(adapted.declared_information[0].kind, StatementKind.DECLARED_INFORMATION)

    def test_assumptions_are_preserved_separately(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertEqual(adapted.to_dict()["metadata"]["legacy_categories"]["assumptions"], ["Une rubrique pourrait être mal paramétrée."])

    def test_assumed_intentions_are_preserved_separately(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertEqual(len(adapted.to_dict()["metadata"]["legacy_categories"]["assumed_intentions"]), 1)

    def test_scenarios_are_preserved_separately(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        self.assertEqual(len(adapted.to_dict()["metadata"]["legacy_categories"]["scenarios"]), 1)

    def test_missing_information_is_converted(self) -> None:
        missing = legacy_payroll_request_to_expert_request(synthetic_request()).missing_information[0]
        self.assertTrue(missing.blocking)
        self.assertIs(missing.criticality, CriticalityLevel.HIGH)

    def test_unknown_legacy_fields_are_preserved(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        unknown = adapted.to_dict()["metadata"]["legacy"]["unknown_fields"]
        self.assertEqual(unknown["custom_legacy_field"], {"preserve": [1, 2, 3]})

    def test_unconverted_field_trace_is_complete(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        records = adapted.to_dict()["metadata"]["legacy"]["unconverted_fields"]
        record = next(item for item in records if item["legacy_field"] == "custom_legacy_field")
        self.assertEqual(
            set(record),
            {"legacy_type", "legacy_field", "legacy_value", "adapter_version", "conversion_status", "conversion_warning"},
        )
        self.assertEqual(record["adapter_version"], "1.0")

    def test_request_json_serialization(self) -> None:
        serialized = legacy_payroll_request_to_expert_request(synthetic_request()).to_dict()
        json.dumps(serialized, ensure_ascii=False, sort_keys=True)

    def test_legacy_new_legacy_round_trip(self) -> None:
        original = synthetic_request()
        restored = expert_request_to_legacy_payroll(legacy_payroll_request_to_expert_request(original))
        self.assertEqual(restored["case_id"], original["case_id"])
        self.assertEqual(restored["custom_legacy_field"], original["custom_legacy_field"])
        self.assertEqual(restored["query"], original["query"])

    def test_new_legacy_new_round_trip(self) -> None:
        original = ExpertRequest(
            "SYN-NEW-1", "Question nouvelle synthétique", "paie",
            facts=(Statement("SYN-F", "Fait synthétique", StatementKind.ESTABLISHED_FACT),),
            confidentiality=ConfidentialityLevel.RESTRICTED,
            metadata={"extension": {"kept": True}},
        )
        restored = legacy_payroll_request_to_expert_request(expert_request_to_legacy_payroll(original))
        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_expert_request_to_historical_public_name(self) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request())
        legacy = expert_request_to_legacy_payroll_request(adapted)
        self.assertEqual(legacy["query"], adapted.question_text)

    def test_input_request_is_not_mutated(self) -> None:
        original = synthetic_request()
        before = copy.deepcopy(original)
        legacy_payroll_request_to_expert_request(original)
        self.assertEqual(original, before)

    def test_request_conversion_is_deterministic(self) -> None:
        first = legacy_payroll_request_to_expert_request(synthetic_request()).to_dict()
        second = legacy_payroll_request_to_expert_request(synthetic_request()).to_dict()
        self.assertEqual(first, second)


class ReportAndSourceAdapterTests(unittest.TestCase):
    def test_minimal_report_is_converted(self) -> None:
        report = legacy_payroll_result_to_expert_report({"request_id": "SYN-MIN-REQ", "active": True})
        self.assertEqual(report.request_id, "SYN-MIN-REQ")
        self.assertEqual(report.producer, "Expert Paie V0")

    def test_complete_report_is_converted(self) -> None:
        legacy = synthetic_report()
        legacy["conclusions"] = ["Conclusion synthétique."]
        legacy["risks"] = [{
            "id": "RISK-COMPLETE", "type": "financial", "description": "Écart synthétique.",
            "level": "MEDIUM", "impact": "Contrôle fictif requis.", "horizon": "court terme",
        }]
        legacy["sources"] = [{
            "name": "Source synthétique prouvée",
            "consultation_evidence": {
                "status": "SUCCEEDED", "occurred_at": "2026-01-10T10:00:00+00:00",
                "exact_reference": "synthetic://source/complete", "access_result": "read_ok",
                "excerpt_or_fingerprint": "sha256:synthetic-complete",
            },
        }]
        report = legacy_payroll_result_to_expert_report(legacy)
        self.assertEqual(len(report.risks), 1)
        self.assertEqual(len(report.sources), 1)
        self.assertEqual(len(report.source_evidence), 1)

    def test_structured_risk_is_converted(self) -> None:
        legacy = synthetic_report()
        legacy["risks"] = [{
            "id": "RISK-SYN-1", "type": "financial", "description": "Écart synthétique possible.",
            "level": "HIGH", "impact": "Rappel fictif à examiner.", "horizon": "court terme",
        }]
        risk = legacy_payroll_report_to_expert_report(legacy).risks[0]
        self.assertIs(risk.level, CriticalityLevel.HIGH)

    def test_low_risk_is_converted(self) -> None:
        risk = legacy_risk_to_risk_assessment({
            "description": "Risque synthétique faible.", "level": "LOW",
            "impact": "Surveillance fictive.", "horizon": "long terme",
        })
        self.assertIs(risk.level, CriticalityLevel.LOW)

    def test_medium_risk_is_converted(self) -> None:
        risk = legacy_risk_to_risk_assessment({
            "description": "Risque synthétique moyen.", "level": "MEDIUM",
            "impact": "Contrôle fictif.", "horizon": "moyen terme",
        })
        self.assertIs(risk.level, CriticalityLevel.MEDIUM)

    def test_critical_risk_requires_explicit_impact(self) -> None:
        legacy = synthetic_report()
        legacy["risks"] = [{"description": "Risque synthétique.", "level": "CRITICAL", "impact": "", "horizon": "immédiat"}]
        with self.assertRaisesRegex(ValueError, "impact"):
            legacy_payroll_report_to_expert_report(legacy)

    def test_free_text_risk_is_not_silently_classified(self) -> None:
        legacy = synthetic_report()
        legacy["risks"] = ["Risque non structuré"]
        with self.assertRaisesRegex(TypeError, "structured mapping"):
            legacy_payroll_report_to_expert_report(legacy)

    def test_missing_risk_level_is_not_defaulted_to_medium(self) -> None:
        legacy = synthetic_report()
        legacy["risks"] = [{
            "description": "Risque synthétique non classé.",
            "impact": "Impact fictif à qualifier.",
            "horizon": "non précisé",
        }]
        with self.assertRaisesRegex(ValueError, "not converted to MEDIUM"):
            legacy_payroll_report_to_expert_report(legacy)

    def test_global_confidence_is_only_analysis_confidence(self) -> None:
        confidence = legacy_payroll_report_to_expert_report(synthetic_report()).confidence_assessments[0]
        self.assertIs(confidence.dimension, ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE)
        self.assertIs(confidence.level, ConfidenceLevel.MEDIUM)

    def test_unknown_confidence_stays_unknown(self) -> None:
        legacy = synthetic_report()
        legacy["niveau_de_confiance"] = "non évaluée"
        confidence = legacy_payroll_report_to_expert_report(legacy).confidence_assessments[0]
        self.assertIsNone(confidence.level)
        self.assertEqual(confidence.raw_value, "non évaluée")

    def test_structured_confidence_keeps_distinct_dimensions(self) -> None:
        legacy = synthetic_report()
        legacy["niveau_de_confiance"] = {
            "factual": "low", "legal": "high", "documentary": "medium",
            "coverage": "unknown", "calculation": "not_assessed", "global": "medium",
        }
        report = legacy_payroll_report_to_expert_report(legacy)
        dimensions = {item.dimension for item in report.confidence_assessments}
        self.assertEqual(dimensions, {
            ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE,
            ConfidenceDimension.LEGAL_SOLIDITY,
            ConfidenceDimension.SOURCE_RELIABILITY,
            ConfidenceDimension.CASE_COMPLETENESS,
        })
        preserved = report.to_dict()["metadata"]["confidence_conversion"]["unmapped_dimensions"]
        self.assertEqual(preserved, {"calculation": "not_assessed", "global": "medium"})

    def test_source_without_proof_is_only_knowledge_source(self) -> None:
        source, evidence = legacy_payroll_source_to_contracts("Accord synthétique")
        self.assertIsNone(evidence)
        self.assertIsNone(source.consulted_at)
        self.assertTrue(source.to_dict()["metadata"]["consultation_not_demonstrated"])

    def test_consulted_source_has_real_evidence(self) -> None:
        source, evidence = legacy_payroll_source_to_contracts({
            "name": "Source officielle synthétique", "is_official": True, "is_internal": False,
            "consultation_evidence": {
                "status": "SUCCEEDED", "occurred_at": "2026-01-10T10:00:00+00:00",
                "exact_reference": "synthetic://official/source/1", "access_result": "read_ok",
                "excerpt_or_fingerprint": "sha256:synthetic-source-1",
            },
        })
        self.assertIsNotNone(evidence)
        self.assertEqual(source.retrieval_evidence_id, evidence.evidence_id)

    def test_false_consultation_proof_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "consultation_evidence"):
            legacy_payroll_source_to_contracts({"name": "Source synthétique", "consulted": True})

    def test_incomplete_consultation_proof_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact_reference"):
            legacy_payroll_source_to_contracts({
                "name": "Source synthétique",
                "consultation_evidence": {"status": "SUCCEEDED", "occurred_at": "2026-01-10T10:00:00+00:00", "access_result": "ok"},
            })

    def test_consultation_without_verifiable_trace_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "excerpt_or_fingerprint"):
            legacy_evidence_to_source_evidence({
                "status": "SUCCEEDED", "occurred_at": "2026-01-10T10:00:00+00:00",
                "exact_reference": "synthetic://source/no-trace", "access_result": "ok",
            }, "SYN-SOURCE-NO-TRACE")

    def test_report_categories_remain_separate(self) -> None:
        legacy = synthetic_report()
        legacy["scenarios"] = ["Scénario synthétique futur."]
        report = legacy_payroll_report_to_expert_report(legacy)
        self.assertIs(report.assumptions[0].kind, StatementKind.ASSUMPTION)
        self.assertIs(report.scenarios[0].kind, StatementKind.SCENARIO)

    def test_report_round_trip_preserves_legacy_extensions(self) -> None:
        original = synthetic_report()
        restored = expert_report_to_legacy_payroll(legacy_payroll_report_to_expert_report(original))
        self.assertEqual(restored["custom_report_field"], original["custom_report_field"])
        self.assertEqual(restored["objet_du_controle"], original["objet_du_controle"])

    def test_new_report_round_trip(self) -> None:
        original = ExpertReport(
            "SYN-NEW-REPORT", "SYN-NEW-REQ", "synthetic",
            conclusions=("Conclusion synthétique prudente.",),
            confidence_assessments=(ConfidenceAssessment(
                "SYN-CONF", ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE,
                ConfidenceLevel.LOW, rationale="Pièces synthétiques incomplètes.",
            ),),
            status=ReportStatus.PARTIAL,
            metadata={"extension": True},
        )
        restored = legacy_payroll_report_to_expert_report(expert_report_to_legacy_payroll(original))
        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_expert_report_to_historical_public_name(self) -> None:
        report = legacy_payroll_report_to_expert_report(synthetic_report())
        legacy = expert_report_to_legacy_payroll_result(report)
        self.assertEqual(legacy["report_id"], report.report_id)

    def test_input_report_is_not_mutated(self) -> None:
        original = synthetic_report()
        before = copy.deepcopy(original)
        legacy_payroll_report_to_expert_report(original)
        self.assertEqual(original, before)

    def test_report_conversion_is_deterministic(self) -> None:
        first = legacy_payroll_report_to_expert_report(synthetic_report()).to_dict()
        second = legacy_payroll_report_to_expert_report(synthetic_report()).to_dict()
        self.assertEqual(first, second)

    def test_collections_are_not_shared(self) -> None:
        report = legacy_payroll_report_to_expert_report(synthetic_report())
        first = expert_report_to_legacy_payroll(report)
        second = expert_report_to_legacy_payroll(report)
        first["limites"].append("Mutation locale synthétique")
        self.assertNotEqual(first["limites"], second["limites"])
        self.assertNotIn("Mutation locale synthétique", report.warnings)


class HistoricalTypesAndScenariosTests(unittest.TestCase):
    def test_payroll_question_round_trip(self) -> None:
        from automation.payroll.payroll_reasoning_protocol import (
            DocumentCategory,
            PayrollQuestion,
            QuestionScope,
        )

        original = PayrollQuestion(
            "Question synthétique", "control", "heures_supplementaires", QuestionScope.EMPLOYEE,
            population="population fictive", period="2026-01",
            available_documents=frozenset({DocumentCategory.PAYSLIP}),
            sources=("Source synthétique",), variables=("overtime_hours",),
        )
        adapted = payroll_question_to_expert_request(original, "SYN-PQ-1")
        restored = expert_request_to_payroll_question(adapted)
        self.assertEqual(restored, original)

    def test_current_paie_payload_remains_compatible(self) -> None:
        from automation.experts import paie

        answer = {
            "query": "Vérifier des heures supplémentaires synthétiques.",
            "route": {"domains": ["paie_remuneration"]},
            "sources": [{"document": "Accord synthétique", "source_layer": "accord_entreprise"}],
            "documents_to_request": [],
            "context": {"variables": {"overtime_hours": 2}, "documents": ["bulletin de paie"]},
        }
        legacy_result = paie.enrich(answer)
        adapted = legacy_payroll_report_to_expert_report(legacy_result, "SYN-COMPAT-1")
        restored = expert_report_to_legacy_payroll(adapted)
        self.assertEqual(restored["active"], legacy_result["active"])
        self.assertEqual(restored["objet_du_controle"], legacy_result["objet_du_controle"])

    def _assert_scenario(self, subject: str) -> None:
        adapted = legacy_payroll_request_to_expert_request(synthetic_request(subject))
        self.assertEqual(adapted.to_dict()["context"]["subject"], subject)

    def test_synthetic_overtime(self) -> None:
        self._assert_scenario("heures_supplementaires")

    def test_synthetic_on_call(self) -> None:
        self._assert_scenario("astreinte")

    def test_synthetic_paid_leave(self) -> None:
        self._assert_scenario("conges_payes")

    def test_synthetic_salary_maintenance(self) -> None:
        self._assert_scenario("maintien_salaire")

    def test_synthetic_public_holiday(self) -> None:
        self._assert_scenario("jour_ferie")

    def test_synthetic_compensatory_rest(self) -> None:
        self._assert_scenario("repos_compensateur")


class DependencyTests(unittest.TestCase):
    def test_adapter_version_is_stable(self) -> None:
        self.assertEqual(ADAPTER_VERSION, "1.0")

    def test_public_api_is_stable(self) -> None:
        import automation.adapters as adapters

        expected = {
            "ADAPTER_VERSION",
            "legacy_payroll_request_to_expert_request",
            "expert_request_to_legacy_payroll_request",
            "legacy_payroll_result_to_expert_report",
            "expert_report_to_legacy_payroll_result",
            "legacy_source_to_knowledge_source",
            "legacy_evidence_to_source_evidence",
            "legacy_missing_information_to_contract",
            "legacy_risk_to_risk_assessment",
            "legacy_confidence_to_confidence_assessment",
        }
        self.assertTrue(expected.issubset(set(adapters.__all__)))
        self.assertIsNotNone(legacy_source_to_knowledge_source("Source synthétique"))
        self.assertIsNotNone(legacy_missing_information_to_contract("Pièce synthétique"))
        self.assertIsNotNone(legacy_confidence_to_confidence_assessment("unknown"))

    def test_no_connector_or_other_engine_import(self) -> None:
        source_path = Path(__file__).with_name("payroll.py")
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = ("connector", "cse_memory", "protection_sociale", "web", "orchestrator", "router")
        self.assertFalse(any(any(token in name for token in forbidden) for name in imports), imports)

    def test_no_network_module_or_call(self) -> None:
        source = Path(__file__).with_name("payroll.py").read_text(encoding="utf-8")
        for token in ("urllib", "requests", "http.client", "socket", "urlopen"):
            self.assertNotIn(token, source)

    def test_import_does_not_load_forbidden_packages(self) -> None:
        for name in list(sys.modules):
            if name.startswith("automation.adapters"):
                sys.modules.pop(name)
        importlib.import_module("automation.adapters.payroll")
        newly_loaded = set(sys.modules)
        forbidden = ("automation.connector_platform", "automation.cse_memory", "automation.protection_sociale")
        self.assertFalse(any(name.startswith(forbidden) for name in newly_loaded))


if __name__ == "__main__":
    unittest.main()
