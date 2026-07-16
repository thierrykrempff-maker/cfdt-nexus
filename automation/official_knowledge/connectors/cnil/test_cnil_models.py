import unittest
from automation.official_knowledge.connectors.cnil.cnil_models import CnilResource,ResourceCandidate,stable_resource_id

class CnilModelTests(unittest.TestCase):
 def test_stable_id_and_canonical_uri(self):
  uri="https://www.cnil.fr/fr/synthetic-work-guidance";self.assertEqual(stable_resource_id(uri),stable_resource_id(uri));self.assertNotIn("C:",stable_resource_id(uri))
 def test_resource_model_and_provenance(self):
  r=CnilResource(stable_resource_id("https://www.cnil.fr/fr/synthetic"),"cnil","https://www.cnil.fr/fr/synthetic","web_guidance","Conseil synthétique",theme_tags=("employee_surveillance",),license_id="CC-BY-ND-4.0-FR",provenance={"source_id":"cnil"})
  self.assertEqual("official_guidance",r.authority_level);self.assertEqual("cnil",r.provenance["source_id"])
 def test_absolute_path_refused(self):
  with self.assertRaises(ValueError):CnilResource("x","cnil","C:/secret","unknown","Synthetic")
 def test_types_news_guide_deliberation_dataset_unknown(self):
  for typ in ("news","guide","deliberation","open_dataset","unknown"):
   with self.subTest(typ=typ):self.assertEqual(typ,ResourceCandidate("https://www.cnil.fr/fr/synthetic",typ).resource_type)
