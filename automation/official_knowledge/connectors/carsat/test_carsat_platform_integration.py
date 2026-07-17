import unittest

from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_contract import ConnectorContract
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ConnectorPlatformError,ErrorCode
from automation.connector_platform.connector_health import HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_states import ConnectorState

from . import CARSAT_NETWORK_NOT_IMPLEMENTED
from .carsat_catalog import DOCUMENT_CATEGORIES,FUNCTIONAL_DOMAINS
from .carsat_contract import CarsatConnector
from .carsat_models import CarsatDocumentCategory,CarsatDocumentFamily,CarsatDocumentIdentity,CarsatFunctionalDomain,CarsatMission
from .carsat_platform import CARSAT_PLATFORM_CONTRACT,CARSAT_REGISTRY,CARSAT_VALIDATION

class CarsatPlatformIntegrationTests(unittest.TestCase):
 def legacy(self):return CarsatDocumentIdentity("SYNTHETIC-001","Synthetic",CarsatDocumentFamily.PREVENTION_GUIDE,CarsatMission.OCCUPATIONAL_RISK_PREVENTION,"2026-01","v1")
 def enriched(self):return CarsatDocumentIdentity("SYNTHETIC-002","Synthetic enriched",CarsatDocumentFamily.PRACTICAL_SHEET,CarsatMission.HEALTH_AT_WORK,"2026-02","v2",CarsatFunctionalDomain.PREVENTION,CarsatDocumentCategory.FICHE)
 def test_platform_contract_source(self):self.assertIsInstance(CarsatConnector.platform_contract,ConnectorContract);self.assertIs(CARSAT_PLATFORM_CONTRACT,CarsatConnector.platform_contract)
 def test_state_unchanged(self):self.assertIs(ConnectorState.ARCHITECTURE_ONLY,CARSAT_PLATFORM_CONTRACT.state)
 def test_facade_unchanged(self):self.assertFalse(CarsatConnector.enabled);self.assertEqual("architecture_only",CarsatConnector.connector_status)
 def test_network_default(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_registry(self):self.assertIsInstance(CARSAT_REGISTRY,ConnectorRegistry);self.assertIs(CARSAT_PLATFORM_CONTRACT,CARSAT_REGISTRY.get("carsat"))
 def test_validation(self):self.assertTrue(CARSAT_VALIDATION.valid);self.assertEqual((),CARSAT_VALIDATION.errors)
 def test_fail_closed(self):self.assertTrue(all(vars(CARSAT_PLATFORM_CONTRACT.security).values()))
 def test_policy(self):self.assertIs(DocumentPolicy.METADATA_ONLY,CARSAT_PLATFORM_CONTRACT.document_policy)
 def test_license(self):self.assertIs(LicenseId.DOCUMENT_SPECIFIC,CARSAT_PLATFORM_CONTRACT.license_id)
 def test_health(self):self.assertIs(HealthStatus.DISABLED,CarsatConnector.health.status)
 def test_statistics_zero(self):self.assertEqual((0,0,0),(CarsatConnector.statistics.document_count,CarsatConnector.statistics.consultation_count,CarsatConnector.statistics.average_duration_ms))
 def test_metrics_zero(self):self.assertTrue(all(metric.value==0 for metric in CarsatConnector.metrics))
 def test_capabilities_still_inactive(self):self.assertEqual({Capability.MANUAL},set(CARSAT_PLATFORM_CONTRACT.capabilities))
 def test_domains_complete(self):self.assertEqual(set(CarsatFunctionalDomain),set(FUNCTIONAL_DOMAINS))
 def test_categories_complete(self):self.assertEqual(set(CarsatDocumentCategory),set(DOCUMENT_CATEGORIES))
 def test_legacy_defaults(self):self.assertIs(CarsatFunctionalDomain.AUTRE,self.legacy().functional_domain);self.assertIs(CarsatDocumentCategory.AUTRE,self.legacy().category)
 def test_legacy_dictionary_accepted(self):
  value=self.legacy().to_dict();value.pop("functional_domain");value.pop("category");self.assertEqual(self.legacy(),CarsatDocumentIdentity.from_dict(value))
 def test_enriched_round_trip(self):value=self.enriched();self.assertEqual(value,CarsatDocumentIdentity.from_dict(value.to_dict()))
 def test_deterministic_serialization(self):self.assertEqual(self.enriched().to_dict(),self.enriched().to_dict())
 def test_invalid_identity_rejected(self):
  with self.assertRaisesRegex(ValueError,"missing document identity field"):CarsatDocumentIdentity.from_dict({"reference":"SYNTHETIC"})
 def test_stable_fingerprint(self):self.assertEqual(self.enriched().fingerprint(),self.enriched().fingerprint())
 def test_legacy_fingerprint_compatibility(self):
  legacy=self.legacy();explicit=CarsatDocumentIdentity(legacy.reference,legacy.title,legacy.family,legacy.mission,legacy.publication_date,legacy.version,CarsatFunctionalDomain.AUTRE,CarsatDocumentCategory.AUTRE);self.assertEqual(legacy.fingerprint(),explicit.fingerprint())
 def test_citation_provenance_and_conversions(self):
  value=self.enriched();citation=value.citation("https://example.invalid/carsat/item");provenance=value.provenance("https://example.invalid/carsat/item");self.assertEqual("CARSAT",citation.author);self.assertTrue(provenance.fingerprint);self.assertIs(DocumentPolicy.METADATA_ONLY,value.platform_policy());self.assertIs(LicenseId.DOCUMENT_SPECIFIC,value.platform_license())
 def test_facade_serialization(self):connector=CarsatConnector();value=self.enriched();self.assertEqual(value,connector.deserialize_identity(connector.serialize_identity(value)))
 def test_operations_blocked_and_runtime_compatible(self):
  connector=CarsatConnector()
  for operation in (lambda:connector.discover("synthetic"),lambda:connector.fetch(self.enriched()),connector.synchronize):
   with self.subTest(operation=operation):
    with self.assertRaises(ConnectorPlatformError) as raised:operation()
    self.assertIsInstance(raised.exception,RuntimeError);self.assertIs(ErrorCode.NETWORK_DISABLED,raised.exception.code);self.assertEqual(CARSAT_NETWORK_NOT_IMPLEMENTED,str(raised.exception))

if __name__=="__main__":unittest.main()
