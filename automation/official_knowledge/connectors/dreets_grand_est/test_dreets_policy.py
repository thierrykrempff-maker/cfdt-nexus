import unittest
from automation.official_knowledge.connectors.dreets_grand_est.dreets_policy import classify_document,default_document_policy

class PolicyTests(unittest.TestCase):
 def test_cse_during_leave_classification(self):
  result=classify_document("CSE pendant les congés");self.assertIn("cse",result.domains);self.assertIn("temps_de_travail",result.domains)
 def test_information_consultation(self): self.assertIn("cse",classify_document("Délais information consultation du comité social et économique").domains)
 def test_protected_employee(self):
  result=classify_document("Licenciement d'un salarié protégé et autorisation de l'inspection du travail");self.assertTrue({"inspection_du_travail","representation_du_personnel","licenciement"}<=set(result.domains))
 def test_classification_never_proves_applicability(self): self.assertTrue(classify_document("Salaire").requires_official_text_check)
 def test_unknown_topic_is_low_confidence(self): self.assertEqual("low",classify_document("Sujet synthétique non classé").confidence_level)
 def test_default_policy_fail_closed_for_each_category(self):
  for category in ("guide","faq","actualité","instruction","circulaire","fiche","publication","dossier","communiqué","formulaire","modèle"):
   policy=default_document_policy(category);self.assertFalse(policy.cache_allowed);self.assertEqual("METADATA_ONLY",policy.index_level)
