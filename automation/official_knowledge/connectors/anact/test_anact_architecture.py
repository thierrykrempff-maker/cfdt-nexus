import inspect
import unittest
from datetime import datetime,timezone

from automation.connector_platform import NETWORK_DISABLED_BY_DEFAULT
from automation.connector_platform.connector_capabilities import Capability
from automation.connector_platform.connector_contract import ConnectorContract
from automation.connector_platform.connector_document import DocumentPolicy
from automation.connector_platform.connector_errors import ConnectorPlatformError,ErrorCode
from automation.connector_platform.connector_health import HealthStatus
from automation.connector_platform.connector_license import LicenseId
from automation.connector_platform.connector_registry import ConnectorRegistry
from automation.connector_platform.connector_states import ConnectorState
from automation.official_knowledge.source_registry import get_source as get_gateway_source

from . import ANACT_NETWORK_NOT_IMPLEMENTED
from .anact_catalog import FAMILY_BY_ID,SOURCE_FAMILIES,SOURCES,get_source
from .anact_contract import AnactConnector
from .anact_models import AccessStatus,AnactResource,AnactResourceType,AnactTheme,ConfidenceLevel,GeographicScope,ValidationStatus
from .anact_platform import ANACT_PLATFORM_CONTRACT,ANACT_REGISTRY,ANACT_VALIDATION

class AnactArchitectureTests(unittest.TestCase):
 def synthetic(self):return AnactResource("synthetic-anact-001","anact_national",AnactResourceType.GUIDE,AnactTheme.QVCT,"Synthetic ANACT resource","https://example.invalid/anact/synthetic",summary="Synthetic test data only",collected_at=datetime(2026,7,17,tzinfo=timezone.utc),author_or_body="Synthetic body",scope=GeographicScope.NATIONAL,validation_status=ValidationStatus.PENDING,confidence=ConfidenceLevel.LOW,synthetic_only=True,official_content=False)
 def test_import_and_contract(self):self.assertIsInstance(AnactConnector.platform_contract,ConnectorContract)
 def test_identity(self):self.assertEqual("anact",AnactConnector.connector_id);self.assertEqual("anact",ANACT_PLATFORM_CONTRACT.metadata.connector_id)
 def test_state_disabled(self):self.assertIs(ConnectorState.ARCHITECTURE_ONLY,ANACT_PLATFORM_CONTRACT.state);self.assertFalse(AnactConnector.enabled);self.assertEqual("architecture_only",AnactConnector.connector_status)
 def test_gateway_registry_remains_disabled(self):value=get_gateway_source("anact");self.assertFalse(value.enabled);self.assertEqual("architecture_only",value.connector_status)
 def test_platform_registry(self):self.assertIsInstance(ANACT_REGISTRY,ConnectorRegistry);self.assertIs(ANACT_PLATFORM_CONTRACT,ANACT_REGISTRY.get("anact"))
 def test_contract_valid(self):self.assertTrue(ANACT_VALIDATION.valid);self.assertEqual((),ANACT_VALIDATION.errors)
 def test_policy_and_license(self):self.assertIs(DocumentPolicy.METADATA_ONLY,ANACT_PLATFORM_CONTRACT.document_policy);self.assertIs(LicenseId.DOCUMENT_SPECIFIC,ANACT_PLATFORM_CONTRACT.license_id)
 def test_network_default(self):self.assertEqual("NETWORK_DISABLED_BY_DEFAULT",NETWORK_DISABLED_BY_DEFAULT)
 def test_fail_closed(self):self.assertTrue(all(vars(ANACT_PLATFORM_CONTRACT.security).values()))
 def test_manual_capability_only(self):self.assertEqual({Capability.MANUAL},set(ANACT_PLATFORM_CONTRACT.capabilities))
 def test_health_statistics_metrics(self):self.assertIs(HealthStatus.DISABLED,AnactConnector.health.status);self.assertEqual((0,0),(AnactConnector.statistics.document_count,AnactConnector.statistics.consultation_count));self.assertTrue(all(metric.value==0 for metric in AnactConnector.metrics))
 def test_catalog_nonempty_and_unique(self):self.assertTrue(SOURCE_FAMILIES);self.assertEqual(len(SOURCE_FAMILIES),len(FAMILY_BY_ID))
 def test_catalog_priorities(self):self.assertTrue(all(1<=value.priority<=5 for value in SOURCE_FAMILIES))
 def test_sources_pending_review(self):self.assertTrue(all(source.access_status is AccessStatus.PENDING_OFFICIAL_REVIEW for source in SOURCES))
 def test_official_root_only(self):self.assertEqual("https://www.anact.fr",get_source("anact_national").official_url)
 def test_unknown_source(self):
  with self.assertRaisesRegex(KeyError,"unknown ANACT source"):get_source("unknown")
 def test_resource_metadata(self):
  value=self.synthetic();self.assertTrue(value.synthetic_only);self.assertFalse(value.official_content);self.assertEqual("fr",value.language);self.assertIsNone(value.published_at)
 def test_deterministic_output(self):self.assertEqual(self.synthetic().to_dict(),self.synthetic().to_dict());self.assertEqual(self.synthetic().fingerprint(),self.synthetic().fingerprint())
 def test_citation_and_provenance(self):value=self.synthetic();self.assertEqual(value.title,value.citation().title);self.assertEqual("anact",value.provenance().source_id);self.assertTrue(value.provenance().fingerprint)
 def test_normalize_is_metadata_only(self):value=self.synthetic();self.assertIs(value,AnactConnector().normalize(value))
 def test_validate_synthetic_resource(self):self.assertTrue(AnactConnector().validate_resource(self.synthetic()).valid)
 def test_validate_unknown_source(self):
  value=self.synthetic();unknown=AnactResource(value.resource_id,"unknown",value.resource_type,value.theme,value.title,value.canonical_url,synthetic_only=True);result=AnactConnector().validate_resource(unknown);self.assertFalse(result.valid);self.assertIn("unknown_source",result.errors)
 def test_invalid_resource(self):
  with self.assertRaises(ValueError):AnactResource("","anact_national",AnactResourceType.GUIDE,AnactTheme.QVCT,"","invalid")
 def test_synthetic_cannot_be_official(self):
  with self.assertRaises(ValueError):AnactResource("x","anact_national",AnactResourceType.GUIDE,AnactTheme.QVCT,"Synthetic","https://example.invalid",synthetic_only=True,official_content=True)
 def test_diagnostic_disabled(self):self.assertIs(HealthStatus.DISABLED,AnactConnector().diagnose().status)
 def test_operations_blocked(self):
  connector=AnactConnector()
  for operation in (lambda:connector.discover("anact_national"),lambda:connector.fetch("synthetic"),connector.synchronize):
   with self.subTest(operation=operation):
    with self.assertRaises(ConnectorPlatformError) as raised:operation()
    self.assertIsInstance(raised.exception,RuntimeError);self.assertIs(ErrorCode.NETWORK_DISABLED,raised.exception.code);self.assertEqual(ANACT_NETWORK_NOT_IMPLEMENTED,str(raised.exception))
 def test_no_expert_engine_imports(self):
  modules=(inspect.getmodule(AnactConnector),inspect.getmodule(AnactResource))
  self.assertTrue(all(module and not any(name.startswith("automation.experts") or name.startswith("automation.payroll") for name in vars(module)) for module in modules))

if __name__=="__main__":unittest.main()
