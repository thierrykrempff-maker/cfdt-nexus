import unittest
from automation.official_knowledge.license_policy import LICENSE_POLICIES,license_capabilities

class LicensePolicyTests(unittest.TestCase):
 def test_all_supported_licenses(self):
  self.assertEqual({"LICENCE_OUVERTE","CC_BY","CC_BY_SA","CC_BY_ND","CC_BY_NC","CC_BY_NC_SA","CC_BY_NC_ND","PUBLIC_DOMAIN","UNKNOWN"},set(LICENSE_POLICIES))
 def test_open_and_public_domain(self):
  for name in ("Licence Ouverte","CC BY","Domaine Public"):
   p=license_capabilities(name);self.assertTrue(p.full_text_allowed);self.assertTrue(p.fulltext_indexing_allowed);self.assertTrue(p.cache_allowed)
 def test_nd_forbids_transformation_and_fulltext_indexing(self):
  p=license_capabilities("CC BY-ND");self.assertFalse(p.transformation_allowed);self.assertFalse(p.fulltext_indexing_allowed);self.assertTrue(p.attribution_required);self.assertTrue(p.legal_review_required)
 def test_noncommercial_variants_are_conservative(self):
  for name in ("CC BY-NC","CC BY-NC-SA","CC BY-NC-ND"):
   p=license_capabilities(name);self.assertFalse(p.redistribution_allowed);self.assertTrue(p.legal_review_required)
 def test_unknown_is_fail_closed(self):
  p=license_capabilities("unrecognized");self.assertFalse(p.full_text_allowed);self.assertFalse(p.cache_allowed);self.assertFalse(p.indexing_allowed);self.assertTrue(p.metadata_indexing_allowed)
