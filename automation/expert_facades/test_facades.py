"""Synthetic acceptance and non-regression controls for ARCH-03."""

from __future__ import annotations

import ast
import copy
import importlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import automation.expert_facades as public_api
from automation.adapters import ADAPTER_VERSION, legacy_payroll_request_to_expert_request
from automation.contracts import (
    ConfidenceLevel,
    ExpertReport,
    ExpertRequest,
    ReportStatus,
    StatementKind,
)

from .base import ExpertFacade, FACADE_API_VERSION, LegacyBusinessRefusal
from .payroll import PAYROLL_CAPABILITIES, PayrollFacade
from .registry import (
    DuplicateExpertError,
    ExpertFacadeRegistry,
    FacadeStatus,
    FacadeUnavailableError,
    UnknownExpertError,
    build_default_registry,
)


PACKAGE_DIR = Path(__file__).resolve().parent


def minimal_request(question: str = "Verifier les heures supplementaires synthetiques") -> ExpertRequest:
    return ExpertRequest("syn-arch03-request", question, "paie", context={"period": "2026-01"})


def complete_request() -> ExpertRequest:
    return legacy_payroll_request_to_expert_request({
        "request_id": "syn-arch03-complete",
        "query": "Verifier des heures supplementaires sur un bulletin fictif",
        "domain": "paie",
        "context": {"period": "2026-01", "variables": {"hours": 2}},
        "facts": [{"id": "fact-syn", "text": "Deux heures fictives sont declarees."}],
        "declarations": [{"id": "decl-syn", "text": "La personne fictive signale un ecart."}],
        "hypotheses": ["Une rubrique fictive pourrait manquer."],
        "scenarios": ["Une regularisation fictive pourrait etre necessaire."],
        "missing_information": [{
            "id": "miss-syn", "description": "Bulletin fictif", "reason": "Controle requis",
            "criticality": "HIGH", "blocking": True, "question": "Fournir le bulletin fictif ?",
        }],
    })


def legacy_result(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "active": True,
        "name": "Expert Paie synthetique",
        "objet_du_controle": "Controle fictif",
        "methode_de_controle": ["Comparer des donnees synthetiques."],
        "niveau_de_confiance": "faible",
    }
    result.update(overrides)
    return result


class StubFacade(ExpertFacade):
    def __init__(self, expert_id: str = "stub") -> None:
        super().__init__(expert_id, ("synthetic",))

    def _execute(self, request: ExpertRequest) -> ExpertReport:
        return ExpertReport(
            report_id=f"report-{request.request_id}", request_id=request.request_id,
            producer=self.expert_id, findings=(request.question_text,), status=ReportStatus.COMPLETED,
        )


class FacadeContractTests(unittest.TestCase):
    def test_create_valid_facade(self) -> None:
        facade = StubFacade()
        self.assertEqual(facade.expert_id, "stub")

    def test_reject_empty_expert_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "expert_id"):
            StubFacade(" ")

    def test_reject_empty_capability(self) -> None:
        with self.assertRaisesRegex(ValueError, "capabilities"):
            ExpertFacade.__init__(StubFacade(), "stub", ("",))

    def test_reject_duplicate_capability(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicates"):
            ExpertFacade.__init__(StubFacade(), "stub", ("same", "same"))

    def test_invalid_request_returns_structured_report(self) -> None:
        report = StubFacade().execute(None)  # type: ignore[arg-type]
        self.assertIs(report.status, ReportStatus.FAILED)
        self.assertEqual(report.request_id, "invalid-request")

    def test_request_is_immutable(self) -> None:
        request = complete_request()
        before = request.to_dict()
        StubFacade().execute(request)
        self.assertEqual(request.to_dict(), before)

    def test_facade_trace_is_added(self) -> None:
        report = StubFacade().execute(minimal_request())
        self.assertEqual(report.to_dict()["metadata"]["facade"]["api_version"], FACADE_API_VERSION)

    def test_programming_error_is_not_silenced(self) -> None:
        class BrokenFacade(StubFacade):
            def _execute(self, request: ExpertRequest) -> ExpertReport:
                raise RuntimeError("synthetic programming fault")

        with self.assertRaisesRegex(RuntimeError, "programming fault"):
            BrokenFacade().execute(minimal_request())

    def test_business_refusal_is_structured(self) -> None:
        class RefusingFacade(StubFacade):
            def _execute(self, request: ExpertRequest) -> ExpertReport:
                raise LegacyBusinessRefusal("synthetic business refusal")

        report = RefusingFacade().execute(minimal_request())
        self.assertIs(report.status, ReportStatus.REFUSED)
        self.assertIn("business refusal", report.errors[0])

    def test_deterministic_facade_result(self) -> None:
        request = minimal_request()
        self.assertEqual(StubFacade().execute(request).to_dict(), StubFacade().execute(request).to_dict())

    def test_json_serialization(self) -> None:
        json.dumps(StubFacade().execute(minimal_request()).to_dict(), sort_keys=True)

    def test_no_shared_metadata_collections(self) -> None:
        first = StubFacade().execute(minimal_request()).to_dict()
        second = StubFacade().execute(minimal_request()).to_dict()
        first["metadata"]["local"] = True
        self.assertNotIn("local", second["metadata"])


class RegistryTests(unittest.TestCase):
    def test_register_and_find_known_facade(self) -> None:
        registry = ExpertFacadeRegistry()
        registry.register(StubFacade())
        self.assertIsInstance(registry.resolve("stub"), StubFacade)

    def test_reject_duplicate_identifier(self) -> None:
        registry = ExpertFacadeRegistry()
        registry.register(StubFacade())
        with self.assertRaises(DuplicateExpertError):
            registry.register(StubFacade())

    def test_refuse_unknown_facade(self) -> None:
        with self.assertRaises(UnknownExpertError):
            ExpertFacadeRegistry().get("unknown")

    def test_unknown_execute_returns_report(self) -> None:
        report = ExpertFacadeRegistry().execute("unknown", minimal_request())
        self.assertEqual(report.to_dict()["metadata"]["facade_error"]["code"], "UNKNOWN_EXPERT")

    def test_list_capabilities(self) -> None:
        registry = ExpertFacadeRegistry()
        registry.register(StubFacade())
        self.assertEqual(registry.list_capabilities(), {"stub": ("synthetic",)})

    def test_available_status(self) -> None:
        self.assertIs(build_default_registry().get("paie").status, FacadeStatus.AVAILABLE)

    def test_partial_status(self) -> None:
        self.assertIs(build_default_registry().get("juriste_travail").status, FacadeStatus.PARTIAL)

    def test_not_ready_status(self) -> None:
        self.assertIs(build_default_registry().get("cse_memory").status, FacadeStatus.NOT_READY)

    def test_disabled_status(self) -> None:
        registry = ExpertFacadeRegistry()
        registry.declare("disabled-synthetic", FacadeStatus.DISABLED)
        self.assertIs(registry.get("disabled-synthetic").status, FacadeStatus.DISABLED)

    def test_not_ready_cannot_resolve(self) -> None:
        with self.assertRaises(FacadeUnavailableError):
            build_default_registry().resolve("protection_sociale")

    def test_disabled_execute_is_refused(self) -> None:
        registry = ExpertFacadeRegistry()
        registry.declare("disabled-synthetic", FacadeStatus.DISABLED)
        self.assertIs(registry.execute("disabled-synthetic", minimal_request()).status, ReportStatus.REFUSED)

    def test_not_ready_execute_is_failed(self) -> None:
        report = build_default_registry().execute("local_law", minimal_request())
        self.assertIs(report.status, ReportStatus.FAILED)

    def test_available_declaration_requires_facade(self) -> None:
        with self.assertRaisesRegex(ValueError, "registered with a facade"):
            ExpertFacadeRegistry().declare("invalid", FacadeStatus.AVAILABLE)

    def test_registrations_are_sorted(self) -> None:
        ids = [item.expert_id for item in build_default_registry().registrations()]
        self.assertEqual(ids, sorted(ids))

    def test_registry_does_not_select_an_expert(self) -> None:
        self.assertFalse(hasattr(ExpertFacadeRegistry, "select"))


class PayrollFacadeTests(unittest.TestCase):
    def test_minimal_payroll_request(self) -> None:
        report = PayrollFacade().execute(minimal_request())
        self.assertEqual(report.request_id, "syn-arch03-request")

    def test_complete_payroll_request(self) -> None:
        report = PayrollFacade().execute(complete_request())
        self.assertTrue(report.findings)

    def test_overtime_scenario(self) -> None:
        self.assertTrue(PayrollFacade().execute(minimal_request("Verifier les heures supplementaires")).findings)

    def test_on_call_scenario(self) -> None:
        self.assertTrue(PayrollFacade().execute(minimal_request("Verifier une astreinte fictive")).findings)

    def test_paid_leave_scenario(self) -> None:
        self.assertTrue(PayrollFacade().execute(minimal_request("Verifier des conges payes fictifs")).findings)

    def test_salary_maintenance_scenario(self) -> None:
        self.assertTrue(PayrollFacade().execute(minimal_request("Verifier un maintien de salaire fictif")).findings)

    def test_public_holiday_scenario(self) -> None:
        self.assertTrue(PayrollFacade().execute(minimal_request("Verifier un jour ferie fictif")).findings)

    def test_compensatory_rest_scenario(self) -> None:
        self.assertTrue(PayrollFacade().execute(minimal_request("Verifier un repos compensateur fictif")).findings)

    def test_identifier_is_preserved(self) -> None:
        self.assertEqual(PayrollFacade().execute(complete_request()).request_id, "syn-arch03-complete")

    def test_facts_are_preserved_in_metadata(self) -> None:
        categories = PayrollFacade().execute(complete_request()).to_dict()["metadata"]["payroll_facade"]["request_categories"]
        self.assertEqual(categories["facts"][0]["kind"], StatementKind.ESTABLISHED_FACT.value)

    def test_declarations_are_preserved_in_metadata(self) -> None:
        categories = PayrollFacade().execute(complete_request()).to_dict()["metadata"]["payroll_facade"]["request_categories"]
        self.assertEqual(categories["declared_information"][0]["kind"], StatementKind.DECLARED_INFORMATION.value)

    def test_assumptions_are_preserved_in_metadata(self) -> None:
        categories = PayrollFacade().execute(complete_request()).to_dict()["metadata"]["payroll_facade"]["request_categories"]
        self.assertEqual(len(categories["assumptions"]), 1)

    def test_missing_information_is_preserved(self) -> None:
        self.assertIn("miss-syn", {item.missing_id for item in PayrollFacade().execute(complete_request()).missing_information})

    def test_risks_are_preserved(self) -> None:
        result = legacy_result(risks=[{
            "id": "risk-syn", "type": "financial", "description": "Synthetic variance",
            "level": "MEDIUM", "impact": "Synthetic review", "horizon": "short",
        }])
        report = PayrollFacade(lambda _: result).execute(minimal_request())
        self.assertEqual(report.risks[0].risk_id, "risk-syn")

    def test_prudent_confidence_is_preserved(self) -> None:
        report = PayrollFacade(lambda _: legacy_result()).execute(minimal_request())
        self.assertIs(report.confidence_assessments[0].level, ConfidenceLevel.LOW)

    def test_non_consulted_source_has_no_evidence(self) -> None:
        report = PayrollFacade(lambda _: legacy_result(sources=[{"name": "Synthetic source"}])).execute(minimal_request())
        self.assertEqual(len(report.sources), 1)
        self.assertEqual(report.source_evidence, ())

    def test_consulted_source_keeps_evidence(self) -> None:
        source = {
            "name": "Synthetic proved source",
            "consultation_evidence": {
                "status": "SUCCEEDED", "occurred_at": "2026-01-10T10:00:00+00:00",
                "exact_reference": "synthetic://arch03/source", "access_result": "read_ok",
                "excerpt_or_fingerprint": "sha256:synthetic-arch03",
            },
        }
        report = PayrollFacade(lambda _: legacy_result(sources=[source])).execute(minimal_request())
        self.assertEqual(len(report.source_evidence), 1)

    def test_malformed_historical_output(self) -> None:
        report = PayrollFacade(lambda _: []) .execute(minimal_request())  # type: ignore[arg-type]
        self.assertIs(report.status, ReportStatus.FAILED)

    def test_historical_business_exception(self) -> None:
        def refusing(_: dict[str, object]) -> dict[str, object]:
            raise LegacyBusinessRefusal("synthetic payroll refusal")

        self.assertIs(PayrollFacade(refusing).execute(minimal_request()).status, ReportStatus.REFUSED)

    def test_inactive_historical_expert_is_refused(self) -> None:
        report = PayrollFacade(lambda _: legacy_result(active=False, reason="outside scope")).execute(minimal_request())
        self.assertIs(report.status, ReportStatus.REFUSED)

    def test_payroll_execution_is_deterministic(self) -> None:
        request = minimal_request()
        self.assertEqual(PayrollFacade().execute(request).to_dict(), PayrollFacade().execute(request).to_dict())

    def test_payroll_request_is_not_mutated(self) -> None:
        request = complete_request()
        before = copy.deepcopy(request.to_dict())
        PayrollFacade().execute(request)
        self.assertEqual(request.to_dict(), before)

    def test_payroll_report_is_json_serializable(self) -> None:
        json.dumps(PayrollFacade().execute(complete_request()).to_dict(), sort_keys=True)

    def test_arch02_adapter_version_is_traced(self) -> None:
        metadata = PayrollFacade().execute(minimal_request()).to_dict()["metadata"]["payroll_facade"]
        self.assertEqual(metadata["adapter_version"], ADAPTER_VERSION)

    def test_no_network_call_is_added(self) -> None:
        with patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
            PayrollFacade().execute(minimal_request())

    def test_capabilities_cover_required_scenarios(self) -> None:
        self.assertEqual(len(PAYROLL_CAPABILITIES), 7)


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_public_api_is_stable(self) -> None:
        expected = {"ExpertFacade", "ExpertFacadeRegistry", "PayrollFacade", "FacadeStatus", "build_default_registry"}
        self.assertTrue(expected.issubset(set(public_api.__all__)))

    def test_arch01_compatibility(self) -> None:
        self.assertIsInstance(PayrollFacade().execute(minimal_request()), ExpertReport)

    def test_arch02_compatibility(self) -> None:
        self.assertEqual(PayrollFacade().execute(minimal_request()).to_dict()["metadata"]["payroll_facade"]["adapter_version"], ADAPTER_VERSION)

    def test_package_has_no_forbidden_direct_import(self) -> None:
        forbidden = {"automation.connector_platform", "automation.cse_memory", "automation.protection_sociale"}
        imported: set[str] = set()
        for path in PACKAGE_DIR.glob("*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
        self.assertFalse(any(name in forbidden for name in imported))

    def test_package_does_not_import_router_or_orchestrator(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in PACKAGE_DIR.glob("*.py") if not path.name.startswith("test_")
        )
        self.assertNotIn("assistant_ds_router", source)
        self.assertNotIn("experts.orchestrator", source)

    def test_modules_import_without_cycle(self) -> None:
        for module in ("automation.expert_facades.base", "automation.expert_facades.payroll", "automation.expert_facades.registry"):
            self.assertIsNotNone(importlib.import_module(module))

    def test_api_version_is_one(self) -> None:
        self.assertEqual(FACADE_API_VERSION, "1.0")


if __name__ == "__main__":
    unittest.main()
