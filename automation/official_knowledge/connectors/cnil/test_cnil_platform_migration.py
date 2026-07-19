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
from automation.official_knowledge.connectors.cnil import CNIL_NETWORK_NOT_IMPLEMENTED
from automation.official_knowledge.connectors.cnil.cnil_connector import CnilConnector
from automation.official_knowledge.connectors.cnil.cnil_models import CnilResource,ResourceCandidate,stable_resource_id
from automation.official_knowledge.connectors.cnil.cnil_platform import CNIL_PLATFORM_CONTRACT,CNIL_PLATFORM_REGISTRY,CNIL_PLATFORM_VALIDATION
from automation.official_knowledge.connectors.cnil.cnil_sync import synchronize

class CnilPlatformMigrationTests(unittest.TestCase):
 def test_connector_uses_platform_contract(self):self.assertIsInstance(CnilConnector.platform_contract,ConnectorContract)
 def test_state_is_disabled_and_activable(self):self.assertIs(ConnectorState.DISABLED,CNIL_PLATFORM_CONTRACT.state)
 def test_source_remains_disabled(self):self.assertFalse(CnilConnector.enabled)
 def test_status_is_disabled(self):self.assertEqual("disabled",CnilConnector.connector_status)
 def test_platform_contract_is_valid(self):self.assertTrue(CNIL_PLATFORM_VALIDATION.valid)
 def test_policy_remains_metadata_only(self):self.assertIs(DocumentPolicy.METADATA_ONLY,CNIL_PLATFORM_CONTRACT.document_policy)
 def test_license_remains_cc_by_nd(self):self.assertIs(LicenseId.CC_BY_ND,CNIL_PLATFORM_CONTRACT.license_id)
 def test_security_is_fail_closed(self):self.assertTrue(all(vars(CNIL_PLATFORM_CONTRACT.security).values()))
 def test_network_default_unchanged(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_capabilities_are_metadata_only(self):self.assertEqual({Capability.HTML,Capability.RSS,Capability.ATOM,Capability.MANUAL},set(CNIL_PLATFORM_CONTRACT.capabilities))
 def test_active_capabilities_are_absent(self):self.assertFalse({Capability.AUTHENTICATION,Capability.CACHE,Capability.SYNC,Capability.DOWNLOAD,Capability.DISCOVERY}&CNIL_PLATFORM_CONTRACT.capabilities)
 def test_registry_is_generic(self):self.assertIsInstance(CNIL_PLATFORM_REGISTRY,ConnectorRegistry)
 def test_registry_contains_only_cnil(self):self.assertEqual(("cnil",),CNIL_PLATFORM_REGISTRY.list_ids())
 def test_candidate_fingerprint_is_deterministic(self):
  value=ResourceCandidate("https://www.cnil.fr/fr/synthetic","guide","Synthetic");self.assertEqual(value.platform_fingerprint(),value.platform_fingerprint())
 def test_candidate_citation_and_provenance(self):
  value=ResourceCandidate("https://www.cnil.fr/fr/synthetic","guide","Synthetic");self.assertEqual("Synthetic",value.to_platform_citation().title);self.assertTrue(value.to_platform_provenance().fingerprint)
 def test_resource_serialization_unchanged(self):
  value=CnilResource(stable_resource_id("https://www.cnil.fr/fr/synthetic"),"cnil","https://www.cnil.fr/fr/synthetic","guide","Synthetic")
  self.assertEqual(set(value.__dataclass_fields__),set(value.to_dict()))
 def test_resource_platform_facades(self):
  value=CnilResource("id","cnil","https://www.cnil.fr/fr/synthetic","guide","Synthetic");self.assertEqual("Synthetic",value.to_platform_citation().title);self.assertTrue(value.to_platform_provenance().fingerprint)
 def test_health_is_disabled(self):self.assertIs(HealthStatus.DISABLED,CnilConnector.health.status)
 def test_statistics_and_metrics_are_zero(self):self.assertEqual((0,0),(CnilConnector.statistics.document_count,CnilConnector.statistics.consultation_count));self.assertTrue(all(item.value==0 for item in CnilConnector.metrics))
 def test_error_is_generic_runtime_compatible(self):
  with self.assertRaises(ConnectorPlatformError) as raised:CnilConnector().discover_resources("synthetic")
  self.assertIsInstance(raised.exception,RuntimeError);self.assertIs(ErrorCode.NETWORK_DISABLED,raised.exception.code);self.assertEqual(CNIL_NETWORK_NOT_IMPLEMENTED,str(raised.exception))
 def test_all_historical_operations_stay_blocked(self):
  connector=CnilConnector()
  for call in (lambda:connector.fetch_resource(None),lambda:connector.validate_resource(None),lambda:connector.parse_resource(None),lambda:synchronize()):
   with self.subTest(call=call):
    with self.assertRaisesRegex(RuntimeError,CNIL_NETWORK_NOT_IMPLEMENTED):call()

if __name__=="__main__":unittest.main()
