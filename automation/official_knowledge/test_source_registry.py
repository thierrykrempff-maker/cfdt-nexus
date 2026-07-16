import unittest
from automation.official_knowledge.source_registry import SOURCE_REGISTRY,list_sources

class RegistryTests(unittest.TestCase):
 def test_eleven_stable_sources(self):
  self.assertEqual(11,len(list_sources()));self.assertEqual(len(SOURCE_REGISTRY),len(set(SOURCE_REGISTRY)))
 def test_disabled_architecture_only(self):
  self.assertTrue(all(not s.enabled and s.connector_status=="architecture_only" for s in list_sources()))
 def test_uninvestigated_sources_do_not_invent_endpoints(self):
  self.assertEqual((),SOURCE_REGISTRY["inrs"].official_domains);self.assertEqual("unknown",SOURCE_REGISTRY["inrs"].source_type)
 def test_cnil_official_domains_are_verified_but_not_enabled(self):
  source=SOURCE_REGISTRY["cnil"];self.assertEqual(("cnil.fr","linc.cnil.fr","data.gouv.fr","legifrance.gouv.fr"),source.official_domains);self.assertFalse(source.enabled)
 def test_existing_domains_are_repository_demonstrated(self):
  self.assertIn("api.piste.gouv.fr",SOURCE_REGISTRY["legifrance"].official_domains)
