import unittest
from automation.official_knowledge.connectors.cnil.cnil_catalog import ACCESS_MECHANISMS,LICENSE_CATEGORIES,THEME_PRIORITIES,VERIFIED_ON
from automation.official_knowledge.source_registry import SOURCE_REGISTRY

class CnilCatalogTests(unittest.TestCase):
 def test_verified_and_unconfirmed_modes_are_explicit(self):
  values={x["mechanism"]:x for x in ACCESS_MECHANISMS};self.assertTrue(values["cnil_targeted_pages"]["verified"]);self.assertFalse(values["public_cnil_api"]["verified"]);self.assertEqual("2026-07-16",VERIFIED_ON)
 def test_license_categories(self):
  self.assertFalse(LICENSE_CATEGORIES["web_text"]["modification"]);self.assertEqual("pending",LICENSE_CATEGORIES["web_text"]["review_status"])
  self.assertFalse(LICENSE_CATEGORIES["images_video"]["full_text_storage"]);self.assertEqual("Licence-Ouverte-2.0-default",LICENSE_CATEGORIES["open_dataset"]["license_id"])
 def test_work_scope_priorities(self):
  self.assertIn("employee_surveillance",THEME_PRIORITIES["priority_high"]);self.assertIn("data_transfers",THEME_PRIORITIES["priority_medium"])
 def test_registry_only_cnil_enriched_but_disabled(self):
  source=SOURCE_REGISTRY["cnil"];self.assertFalse(source.enabled);self.assertEqual("architecture_only",source.connector_status);self.assertIn("cnil.fr",source.official_domains)
