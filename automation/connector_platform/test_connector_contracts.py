import unittest
from .connector_capabilities import Capability
from .connector_contract import ConnectorContract
from .connector_document import DocumentPolicy,stores_text
from .connector_license import LICENSE_POLICIES,LicenseId
from .connector_metadata import ConnectorMetadata
from .connector_security import DEFAULT_SECURITY_POLICY,SecurityPolicy
from .connector_states import ConnectorState,can_transition
from .connector_validation import validate_contract

def metadata():return ConnectorMetadata("synthetic_source","Synthetic source","Example public body")

class ContractTests(unittest.TestCase):
 def test_default_contract_is_inactive(self):
  value=ConnectorContract(metadata());self.assertFalse(value.enabled);self.assertEqual(ConnectorState.ARCHITECTURE_ONLY,value.state)
 def test_safe_capabilities_are_declarable(self):self.assertEqual(frozenset({Capability.HTML}),ConnectorContract(metadata(),capabilities=frozenset({Capability.HTML})).capabilities)
 def test_authentication_capability_is_refused(self):
  with self.assertRaises(ValueError):ConnectorContract(metadata(),capabilities=frozenset({Capability.AUTHENTICATION}))
 def test_sync_capability_is_refused(self):
  with self.assertRaises(ValueError):ConnectorContract(metadata(),capabilities=frozenset({Capability.SYNC}))
 def test_download_capability_is_refused(self):
  with self.assertRaises(ValueError):ConnectorContract(metadata(),capabilities=frozenset({Capability.DOWNLOAD}))
 def test_enabled_flag_is_refused(self):
  with self.assertRaises(ValueError):ConnectorContract(metadata(),enabled=True)
 def test_enabled_state_is_refused(self):
  with self.assertRaises(ValueError):ConnectorContract(metadata(),state=ConnectorState.ENABLED)
 def test_unknown_license_accepts_metadata(self):self.assertTrue(validate_contract(ConnectorContract(metadata())).valid)
 def test_unknown_license_rejects_excerpts(self):self.assertFalse(validate_contract(ConnectorContract(metadata(),document_policy=DocumentPolicy.EXCERPTS)).valid)
 def test_all_licenses_have_policy(self):self.assertEqual(set(LicenseId),set(LICENSE_POLICIES))
 def test_nd_never_allows_fulltext(self):self.assertNotEqual(DocumentPolicy.FULLTEXT_ALLOWED,LICENSE_POLICIES[LicenseId.CC_BY_ND].maximum_policy)
 def test_unknown_requires_review(self):self.assertTrue(LICENSE_POLICIES[LicenseId.UNKNOWN].review_required)
 def test_document_specific_requires_review(self):self.assertTrue(LICENSE_POLICIES[LicenseId.DOCUMENT_SPECIFIC].review_required)
 def test_metadata_does_not_store_text(self):self.assertFalse(stores_text(DocumentPolicy.METADATA_ONLY))
 def test_forbidden_does_not_store_text(self):self.assertFalse(stores_text(DocumentPolicy.FORBIDDEN))
 def test_excerpts_store_text(self):self.assertTrue(stores_text(DocumentPolicy.EXCERPTS))
 def test_fulltext_stores_text(self):self.assertTrue(stores_text(DocumentPolicy.FULLTEXT_ALLOWED))
 def test_security_defaults_all_true(self):self.assertTrue(all(vars(DEFAULT_SECURITY_POLICY).values()))
 def test_security_cannot_be_weakened(self):
  with self.assertRaises(ValueError):SecurityPolicy(no_post=False)
 def test_transition_forward(self):self.assertTrue(can_transition(ConnectorState.ARCHITECTURE_ONLY,ConnectorState.ACCESS_REVIEW_COMPLETE))
 def test_transition_skip_refused(self):self.assertFalse(can_transition(ConnectorState.ARCHITECTURE_ONLY,ConnectorState.IMPLEMENTED))
