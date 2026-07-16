import unittest
from automation.official_knowledge.connectors.dreets_grand_est.dreets_catalog import ACCESS_STUDY,DOMAIN_FAMILIES,LICENSE_STUDY,OFFICIAL_DOMAIN,QUESTION_INTENTS

class CatalogTests(unittest.TestCase):
 def test_official_domain_is_scoped(self): self.assertEqual("grand-est.dreets.gouv.fr",OFFICIAL_DOMAIN)
 def test_access_modes_preserve_evidence_status(self):
  by_mode={item["mechanism"]:item for item in ACCESS_STUDY}
  self.assertEqual(by_mode["targeted_official_pages"]["status"],"officially_observed")
  self.assertTrue(by_mode["targeted_official_pages"]["recommended"])
  self.assertEqual(by_mode["official_api"]["status"],"not_identified_in_limited_review")
  self.assertFalse(by_mode["official_api"]["recommended"])
  self.assertFalse(by_mode["rss_or_atom"]["recommended"])
  self.assertFalse(by_mode["sitemap"]["recommended"])
 def test_no_endpoint_is_inferred(self): self.assertTrue(all("url" not in item and "uri" not in item for item in ACCESS_STUDY))
 def test_licenses_fail_closed(self): self.assertTrue(all(not item["cache"] and not item["full_text"] and item["index_level"]=="METADATA_ONLY" for item in LICENSE_STUDY.values()))
 def test_twenty_domain_families(self): self.assertEqual(20,len(DOMAIN_FAMILIES))
 def test_required_domains_present(self): self.assertTrue({"inspection_du_travail","cse","sante_au_travail","dialogue_social","temps_de_travail","licenciement","harcelement","travailleurs_etrangers","questions_reponses_officielles"}<=set(DOMAIN_FAMILIES))
 def test_future_questions_have_intents(self): self.assertEqual({"cse_during_leave","information_consultation_deadlines","protected_employee_rights"},set(QUESTION_INTENTS))
