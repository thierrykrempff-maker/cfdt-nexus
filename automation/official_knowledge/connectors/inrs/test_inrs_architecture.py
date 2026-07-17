import unittest
from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_contract import ConnectorContract
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ConnectorPlatformError
from automation.connector_platform.connector_health import HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_states import ConnectorState
from automation.official_knowledge.source_registry import get_source
from . import INRS_NETWORK_NOT_IMPLEMENTED
from .inrs_catalog import ACCESS_EVIDENCE,FAMILY_PROFILES,IDENTIFIER_FAMILIES
from .inrs_contract import InrsConnector
from .inrs_models import EvidenceStatus,InrsDocumentIdentity,ResourceFamily
from .inrs_platform import INRS_PLATFORM_CONTRACT,INRS_REGISTRY,INRS_VALIDATION

class InrsArchitectureTests(unittest.TestCase):
 def test_platform_contract_used(self):self.assertIsInstance(InrsConnector.platform_contract,ConnectorContract)
 def test_state_architecture_only(self):self.assertIs(ConnectorState.ARCHITECTURE_ONLY,INRS_PLATFORM_CONTRACT.state)
 def test_connector_disabled(self):self.assertFalse(InrsConnector.enabled);self.assertEqual("architecture_only",InrsConnector.connector_status)
 def test_source_registry_still_disabled(self):
  value=get_source("inrs");self.assertFalse(value.enabled);self.assertEqual("architecture_only",value.connector_status)
 def test_network_default(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_metadata_only(self):self.assertIs(DocumentPolicy.METADATA_ONLY,INRS_PLATFORM_CONTRACT.document_policy)
 def test_document_specific_license(self):self.assertIs(LicenseId.DOCUMENT_SPECIFIC,INRS_PLATFORM_CONTRACT.license_id)
 def test_contract_valid(self):self.assertTrue(INRS_VALIDATION.valid)
 def test_only_documentary_capabilities(self):self.assertEqual({Capability.HTML,Capability.PDF,Capability.MANUAL},set(INRS_PLATFORM_CONTRACT.capabilities))
 def test_no_active_capabilities(self):self.assertFalse({Capability.API,Capability.AUTHENTICATION,Capability.CACHE,Capability.SYNC,Capability.DOWNLOAD,Capability.DISCOVERY}&INRS_PLATFORM_CONTRACT.capabilities)
 def test_security_fail_closed(self):self.assertTrue(all(vars(INRS_PLATFORM_CONTRACT.security).values()))
 def test_registry_contains_only_inrs(self):self.assertEqual(("inrs",),INRS_REGISTRY.list_ids())
 def test_health_disabled(self):self.assertIs(HealthStatus.DISABLED,InrsConnector.health.status)
 def test_statistics_and_metrics_zero(self):self.assertEqual((0,0),(InrsConnector.statistics.document_count,InrsConnector.statistics.consultation_count));self.assertTrue(all(item.value==0 for item in InrsConnector.metrics))
 def test_all_operations_blocked(self):
  value=InrsConnector()
  for call in (lambda:value.discover("synthetic"),lambda:value.fetch(None),lambda:value.synchronize()):
   with self.subTest(call=call):
    with self.assertRaisesRegex(RuntimeError,INRS_NETWORK_NOT_IMPLEMENTED):call()
 def test_generic_error_runtime_compatible(self):
  with self.assertRaises(ConnectorPlatformError):InrsConnector().discover("synthetic")
 def test_all_required_families(self):self.assertEqual(set(ResourceFamily),{item.family for item in FAMILY_PROFILES})
 def test_priorities_bounded(self):self.assertTrue(all(1<=item.priority<=5 for item in FAMILY_PROFILES))
 def test_cssct_and_hse_high_priority(self):self.assertTrue(all(item.cssct_interest in {"medium","high","very_high"} and item.hse_interest in {"medium","high","very_high"} for item in FAMILY_PROFILES))
 def test_evidence_never_operational(self):self.assertTrue(all(not item.operational for item in ACCESS_EVIDENCE))
 def test_api_not_identified(self):self.assertEqual(EvidenceStatus.NOT_IDENTIFIED_IN_LIMITED_REVIEW,next(item for item in ACCESS_EVIDENCE if item.mechanism=="public_api").status)
 def test_rss_not_validated(self):self.assertEqual(EvidenceStatus.OBSERVED_NOT_VALIDATED,next(item for item in ACCESS_EVIDENCE if item.mechanism=="rss").status)
 def test_identifiers_include_ed_and_tj(self):self.assertTrue({"ED","TJ"}<=set(IDENTIFIER_FAMILIES))
 def test_identity_serialization_and_fingerprint(self):
  value=InrsDocumentIdentity("ED 0000","Synthetic",ResourceFamily.BROCHURE,"2026-01",None);self.assertEqual("ED 0000",value.to_dict()["reference"]);self.assertEqual(value.fingerprint(),value.fingerprint())
 def test_identity_citation_and_provenance(self):
  value=InrsDocumentIdentity("ED 0000","Synthetic",ResourceFamily.BROCHURE);url="https://example.invalid/inrs/synthetic";self.assertEqual("Synthetic",value.citation(url).title);self.assertTrue(value.provenance(url).fingerprint)

if __name__=="__main__":unittest.main()
