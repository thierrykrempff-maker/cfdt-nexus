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
from .carsat_catalog import ACCESS_POSSIBILITIES,DOCUMENT_FAMILIES,MISSIONS
from .carsat_contract import CarsatConnector
from .carsat_models import AccessReviewStatus,CarsatDocumentFamily,CarsatDocumentIdentity,CarsatMission
from .carsat_platform import CARSAT_PLATFORM_CONTRACT,CARSAT_REGISTRY,CARSAT_VALIDATION

class CarsatArchitectureTests(unittest.TestCase):
 def synthetic(self):return CarsatDocumentIdentity("SYNTHETIC-001","Synthetic",CarsatDocumentFamily.PREVENTION_GUIDE,CarsatMission.OCCUPATIONAL_RISK_PREVENTION,"2026-01","v1")
 def test_platform_contract(self):self.assertIsInstance(CarsatConnector.platform_contract,ConnectorContract)
 def test_state(self):self.assertIs(ConnectorState.ARCHITECTURE_ONLY,CARSAT_PLATFORM_CONTRACT.state)
 def test_legacy_facade(self):self.assertFalse(CarsatConnector.enabled);self.assertEqual("architecture_only",CarsatConnector.connector_status)
 def test_network_default(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_policy(self):self.assertIs(DocumentPolicy.METADATA_ONLY,CARSAT_PLATFORM_CONTRACT.document_policy)
 def test_license(self):self.assertIs(LicenseId.DOCUMENT_SPECIFIC,CARSAT_PLATFORM_CONTRACT.license_id)
 def test_validation(self):self.assertTrue(CARSAT_VALIDATION.valid);self.assertEqual((),CARSAT_VALIDATION.errors)
 def test_registry(self):self.assertIsInstance(CARSAT_REGISTRY,ConnectorRegistry);self.assertEqual(("carsat",),CARSAT_REGISTRY.list_ids());self.assertIs(CARSAT_PLATFORM_CONTRACT,CARSAT_REGISTRY.get("carsat"))
 def test_fail_closed(self):self.assertTrue(all(vars(CARSAT_PLATFORM_CONTRACT.security).values()))
 def test_manual_capability_only(self):self.assertEqual({Capability.MANUAL},set(CARSAT_PLATFORM_CONTRACT.capabilities))
 def test_no_active_capabilities(self):self.assertFalse({Capability.API,Capability.RSS,Capability.ATOM,Capability.HTML,Capability.SITEMAP,Capability.PDF,Capability.OPEN_DATA,Capability.AUTHENTICATION,Capability.CACHE,Capability.SYNC,Capability.DISCOVERY,Capability.SEARCH,Capability.DOWNLOAD,Capability.VERSIONING}&CARSAT_PLATFORM_CONTRACT.capabilities)
 def test_health_disabled(self):self.assertIs(HealthStatus.DISABLED,CarsatConnector.health.status)
 def test_statistics_zero(self):self.assertEqual((0,0,0),(CarsatConnector.statistics.document_count,CarsatConnector.statistics.consultation_count,CarsatConnector.statistics.average_duration_ms))
 def test_metrics_zero(self):self.assertTrue(all(metric.value==0 for metric in CarsatConnector.metrics))
 def test_all_missions_catalogued(self):self.assertEqual(set(CarsatMission),set(MISSIONS))
 def test_all_families_catalogued(self):self.assertEqual(set(CarsatDocumentFamily),set(DOCUMENT_FAMILIES))
 def test_access_pending(self):self.assertTrue(all(item.status is AccessReviewStatus.PENDING_OFFICIAL_REVIEW and not item.operational for item in ACCESS_POSSIBILITIES))
 def test_access_topics_complete(self):self.assertEqual({"api","rss","html","pdf","open_data","manual"},{item.mechanism for item in ACCESS_POSSIBILITIES})
 def test_round_trip(self):value=self.synthetic();self.assertEqual(value,CarsatDocumentIdentity.from_dict(value.to_dict()))
 def test_required_fields(self):
  with self.assertRaisesRegex(ValueError,"missing document identity field"):CarsatDocumentIdentity.from_dict({"title":"Synthetic"})
 def test_fingerprint(self):self.assertEqual(self.synthetic().fingerprint(),self.synthetic().fingerprint())
 def test_platform_conversions(self):self.assertIs(DocumentPolicy.METADATA_ONLY,self.synthetic().platform_policy());self.assertIs(LicenseId.DOCUMENT_SPECIFIC,self.synthetic().platform_license())
 def test_citation(self):value=self.synthetic().citation("https://example.invalid/carsat/item");self.assertEqual(("CARSAT","DOCUMENT_SPECIFIC"),(value.author,value.license_id))
 def test_provenance(self):value=self.synthetic().provenance("https://example.invalid/carsat/item");self.assertEqual("carsat",value.source_id);self.assertTrue(value.fingerprint)
 def test_operations_blocked(self):
  connector=CarsatConnector()
  for operation in (lambda:connector.discover("synthetic"),lambda:connector.fetch(self.synthetic()),connector.synchronize):
   with self.subTest(operation=operation):
    with self.assertRaises(ConnectorPlatformError) as raised:operation()
    self.assertIsInstance(raised.exception,RuntimeError);self.assertIs(ErrorCode.NETWORK_DISABLED,raised.exception.code);self.assertEqual(CARSAT_NETWORK_NOT_IMPLEMENTED,str(raised.exception))

if __name__=="__main__":unittest.main()
