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
from automation.official_knowledge.connectors.dreets_grand_est import DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED
from automation.official_knowledge.connectors.dreets_grand_est.dreets_connector import DreetsGrandEstConnector
from automation.official_knowledge.connectors.dreets_grand_est.dreets_models import DreetsDocumentType,DreetsResourceCandidate
from automation.official_knowledge.connectors.dreets_grand_est.dreets_platform import DREETS_PLATFORM_CONTRACT,DREETS_REGISTRY,DREETS_VALIDATION

class DreetsPlatformMigrationTests(unittest.TestCase):
 def test_connector_uses_platform_contract(self):self.assertIsInstance(DreetsGrandEstConnector.platform_contract,ConnectorContract)
 def test_state_is_architecture_only(self):self.assertIs(ConnectorState.ARCHITECTURE_ONLY,DREETS_PLATFORM_CONTRACT.state)
 def test_legacy_status_is_unchanged(self):self.assertEqual("architecture_only",DreetsGrandEstConnector.connector_status)
 def test_legacy_enabled_is_unchanged(self):self.assertFalse(DreetsGrandEstConnector.enabled)
 def test_platform_contract_is_valid(self):self.assertTrue(DREETS_VALIDATION.valid)
 def test_license_is_unknown(self):self.assertIs(LicenseId.UNKNOWN,DREETS_PLATFORM_CONTRACT.license_id)
 def test_policy_is_metadata_only(self):self.assertIs(DocumentPolicy.METADATA_ONLY,DREETS_PLATFORM_CONTRACT.document_policy)
 def test_security_is_fail_closed(self):self.assertTrue(all(vars(DREETS_PLATFORM_CONTRACT.security).values()))
 def test_network_default_constant(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_no_active_capabilities(self):self.assertFalse({Capability.AUTHENTICATION,Capability.CACHE,Capability.SYNC,Capability.DOWNLOAD}&DREETS_PLATFORM_CONTRACT.capabilities)
 def test_declared_capabilities_are_documentary(self):self.assertEqual({Capability.HTML,Capability.RSS,Capability.SITEMAP,Capability.PDF,Capability.MANUAL},set(DREETS_PLATFORM_CONTRACT.capabilities))
 def test_registry_is_platform_registry(self):self.assertIsInstance(DREETS_REGISTRY,ConnectorRegistry)
 def test_registry_contains_only_dreets(self):self.assertEqual(("dreets_grand_est",),DREETS_REGISTRY.list_ids())
 def test_health_is_disabled(self):self.assertIs(HealthStatus.DISABLED,DreetsGrandEstConnector.health.status)
 def test_statistics_remain_zero(self):self.assertEqual((0,0),(DreetsGrandEstConnector.statistics.document_count,DreetsGrandEstConnector.statistics.consultation_count))
 def test_metrics_remain_zero(self):self.assertTrue(all(metric.value==0 for metric in DreetsGrandEstConnector.metrics))
 def test_legacy_document_policy_converts_to_platform(self):self.assertIs(DocumentPolicy.METADATA_ONLY,DreetsDocumentType("guide","official_guidance","pending").to_platform_policy())
 def test_legacy_license_converts_to_platform(self):self.assertIs(LicenseId.UNKNOWN,DreetsDocumentType("guide","official_guidance","pending").to_platform_license())
 def test_candidate_creates_platform_citation(self):
  value=DreetsResourceCandidate("dreets_grand_est","https://example.invalid/item","Synthetic","fiche",("cse",));self.assertEqual(value.title,value.to_platform_citation().title)
 def test_candidate_creates_platform_provenance(self):
  value=DreetsResourceCandidate("dreets_grand_est","https://example.invalid/item","Synthetic","fiche",("cse",));self.assertTrue(value.to_platform_provenance().fingerprint)
 def test_network_error_is_platform_error_and_runtime_error(self):
  with self.assertRaises(ConnectorPlatformError) as raised:DreetsGrandEstConnector().discover_resources("synthetic")
  self.assertIsInstance(raised.exception,RuntimeError);self.assertIs(ErrorCode.NETWORK_DISABLED,raised.exception.code)
  self.assertEqual(DREETS_GRAND_EST_NETWORK_NOT_IMPLEMENTED,str(raised.exception))

if __name__=="__main__":unittest.main()
