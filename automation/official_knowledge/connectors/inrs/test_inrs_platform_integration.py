import unittest

from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ConnectorPlatformError,ErrorCode
from automation.connector_platform.connector_health import HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_states import ConnectorState

from . import INRS_NETWORK_NOT_IMPLEMENTED
from .inrs_catalog import SUPPORTED_DOCUMENT_TYPES,document_type_for_reference
from .inrs_contract import InrsConnector
from .inrs_models import InrsDocumentIdentity,InrsDocumentType,ResourceFamily
from .inrs_platform import INRS_PLATFORM_CONTRACT,INRS_REGISTRY,INRS_VALIDATION

class InrsPlatformIntegrationTests(unittest.TestCase):
 def synthetic(self):return InrsDocumentIdentity("ED 0000","Synthetic",ResourceFamily.BROCHURE,"2026-01","v1",InrsDocumentType.ED)
 def test_state_unchanged(self):self.assertIs(ConnectorState.ARCHITECTURE_ONLY,INRS_PLATFORM_CONTRACT.state)
 def test_connector_disabled(self):self.assertFalse(InrsConnector.enabled);self.assertEqual("architecture_only",InrsConnector.connector_status)
 def test_network_default_unchanged(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_policy_unchanged(self):self.assertIs(DocumentPolicy.METADATA_ONLY,INRS_PLATFORM_CONTRACT.document_policy)
 def test_license_document_specific(self):self.assertIs(LicenseId.DOCUMENT_SPECIFIC,INRS_PLATFORM_CONTRACT.license_id)
 def test_contract_valid(self):self.assertTrue(INRS_VALIDATION.valid);self.assertEqual((),INRS_VALIDATION.errors)
 def test_registry_generic(self):self.assertIsInstance(INRS_REGISTRY,ConnectorRegistry);self.assertEqual(("inrs",),INRS_REGISTRY.list_ids())
 def test_registry_contract_identity(self):self.assertIs(INRS_PLATFORM_CONTRACT,INRS_REGISTRY.get("inrs"))
 def test_security_fail_closed(self):self.assertTrue(all(vars(INRS_PLATFORM_CONTRACT.security).values()))
 def test_no_forbidden_capabilities(self):self.assertFalse({Capability.API,Capability.RSS,Capability.ATOM,Capability.SITEMAP,Capability.OPEN_DATA,Capability.AUTHENTICATION,Capability.CACHE,Capability.SYNC,Capability.DISCOVERY,Capability.SEARCH,Capability.DOWNLOAD,Capability.VERSIONING}&INRS_PLATFORM_CONTRACT.capabilities)
 def test_documentary_capabilities_only(self):self.assertEqual({Capability.HTML,Capability.PDF,Capability.MANUAL},set(INRS_PLATFORM_CONTRACT.capabilities))
 def test_health_disabled(self):self.assertIs(HealthStatus.DISABLED,InrsConnector.health.status)
 def test_statistics_zero(self):self.assertEqual((0,0,0),(InrsConnector.statistics.document_count,InrsConnector.statistics.consultation_count,InrsConnector.statistics.average_duration_ms))
 def test_metrics_zero(self):self.assertTrue(all(metric.value==0 for metric in InrsConnector.metrics))
 def test_supported_types_complete(self):self.assertEqual(set(InrsDocumentType),set(SUPPORTED_DOCUMENT_TYPES))
 def test_reference_types(self):
  for reference,expected in (("ED 1",InrsDocumentType.ED),("TJ-2",InrsDocumentType.TJ),("AD 3",InrsDocumentType.AD),("AR-4",InrsDocumentType.AR)):
   with self.subTest(reference=reference):self.assertIs(expected,document_type_for_reference(reference))
 def test_unknown_reference(self):self.assertIs(InrsDocumentType.AUTRE,document_type_for_reference("X 1"))
 def test_identity_round_trip(self):
  value=self.synthetic();self.assertEqual(value,InrsDocumentIdentity.from_dict(value.to_dict()))
 def test_missing_identity_field_rejected(self):
  with self.assertRaisesRegex(ValueError,"missing document identity field"):InrsDocumentIdentity.from_dict({"title":"Synthetic"})
 def test_platform_conversions(self):self.assertIs(DocumentPolicy.METADATA_ONLY,self.synthetic().platform_policy());self.assertIs(LicenseId.DOCUMENT_SPECIFIC,self.synthetic().platform_license())
 def test_fingerprint_deterministic(self):self.assertEqual(self.synthetic().fingerprint(),self.synthetic().fingerprint())
 def test_citation_complete(self):
  value=self.synthetic().citation("https://example.invalid/inrs/ed-0000");self.assertEqual(("INRS","DOCUMENT_SPECIFIC","high"),(value.author,value.license_id,value.confidence))
 def test_provenance_complete(self):
  value=self.synthetic().provenance("https://example.invalid/inrs/ed-0000");self.assertEqual("inrs",value.source_id);self.assertTrue(value.fingerprint)
 def test_facade_serialization(self):
  connector=InrsConnector();value=self.synthetic();self.assertEqual(value,connector.deserialize_identity(connector.serialize_identity(value)))
 def test_all_operations_still_blocked(self):
  connector=InrsConnector()
  for operation in (lambda:connector.discover("synthetic"),lambda:connector.fetch(self.synthetic()),connector.synchronize):
   with self.subTest(operation=operation):
    with self.assertRaises(ConnectorPlatformError) as raised:operation()
    self.assertIsInstance(raised.exception,RuntimeError);self.assertIs(ErrorCode.NETWORK_DISABLED,raised.exception.code);self.assertEqual(INRS_NETWORK_NOT_IMPLEMENTED,str(raised.exception))

if __name__=="__main__":unittest.main()
