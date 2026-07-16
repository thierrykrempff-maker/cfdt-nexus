import unittest
from automation.official_knowledge.source_registry import CATALOG_SOURCE_IDS,SOURCE_REGISTRY,list_sources

class RegistryTests(unittest.TestCase):
 def test_fifteen_stable_sources(self):
  self.assertEqual(15,len(list_sources()));self.assertEqual(len(SOURCE_REGISTRY),len(set(SOURCE_REGISTRY)))
 def test_disabled_architecture_only(self):
  self.assertTrue(all(not s.enabled and s.connector_status=="architecture_only" for s in list_sources()))
 def test_uninvestigated_sources_do_not_invent_endpoints(self):
  self.assertEqual((),SOURCE_REGISTRY["inrs"].official_domains);self.assertEqual("unknown",SOURCE_REGISTRY["inrs"].source_type)
 def test_cnil_official_domains_are_verified_but_not_enabled(self):
  source=SOURCE_REGISTRY["cnil"];self.assertEqual(("cnil.fr","linc.cnil.fr","data.gouv.fr","legifrance.gouv.fr"),source.official_domains);self.assertFalse(source.enabled)
 def test_existing_domains_are_repository_demonstrated(self):
  self.assertIn("api.piste.gouv.fr",SOURCE_REGISTRY["legifrance"].official_domains)
 def test_alsace_moselle_authorities_are_separate_and_disabled(self):
  expected={"alsace_moselle_local_law":"primary_law","alsace_moselle_case_law":"official_case_law","dreets_grand_est_local_law":"official_guidance","service_public_local_law":"official_practical_information"}
  for source_id,authority in expected.items():
   source=SOURCE_REGISTRY[source_id];self.assertEqual(authority,source.authority_level);self.assertFalse(source.enabled);self.assertEqual("architecture_only",source.connector_status)
 def test_prioritized_catalog_is_visible_without_activation(self):
  self.assertIn("dreal_grand_est",CATALOG_SOURCE_IDS);self.assertIn("france_chimie",CATALOG_SOURCE_IDS);self.assertTrue(all(not source.enabled for source in list_sources()))
