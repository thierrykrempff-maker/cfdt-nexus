import unittest
from . import ALSACE_MOSELLE_HEALTH_INSURANCE_REGIME,ALSACE_MOSELLE_LOCAL_LAW
from .alsace_moselle_models import EmploymentContext
from .reasoning_guard import evaluate_local_law_check

class GuardTests(unittest.TestCase):
 def test_standard_question_outside_zone_does_not_trigger(self): self.assertFalse(evaluate_local_law_check("Quel est mon salaire ?",EmploymentContext(habitual_work_department="75")).local_law_check_required)
 def test_sarralbe_sickness_triggers(self): self.assertTrue(evaluate_local_law_check("Arrêt maladie à Sarralbe").local_law_check_required)
 def test_moselle_context_triggers_relevant_question(self): self.assertIn(ALSACE_MOSELLE_LOCAL_LAW,evaluate_local_law_check("Maintien de salaire",EmploymentContext(habitual_work_department="57")).local_law_domains_to_check)
 def test_accident_in_local_zone_is_not_ignored(self): self.assertTrue(evaluate_local_law_check("Accident",EmploymentContext(habitual_work_department="67")).local_law_check_required)
 def test_december_26_and_good_friday_trigger(self):
  self.assertTrue(evaluate_local_law_check("Travail le 26 décembre en Moselle").local_law_check_required);self.assertTrue(evaluate_local_law_check("Vendredi saint en Alsace").local_law_check_required)
 def test_notice_triggers_only_with_territorial_signal(self):
  self.assertTrue(evaluate_local_law_check("Préavis en Moselle").local_law_check_required);self.assertFalse(evaluate_local_law_check("Préavis",EmploymentContext(habitual_work_department="75")).local_law_check_required)
 def test_health_regime_is_distinct(self):
  result=evaluate_local_law_check("Suis-je affilié au régime local d'assurance maladie ?");self.assertEqual((ALSACE_MOSELLE_HEALTH_INSURANCE_REGIME,),result.local_law_domains_to_check);self.assertIn("health_insurance_regime_does_not_prove_local_employment_law",result.warnings)
 def test_head_office_alone_does_not_trigger_irrelevant_question(self): self.assertFalse(evaluate_local_law_check("Télétravail",EmploymentContext(employer_head_office_department="57")).local_law_check_required)
 def test_missing_place_is_reported(self): self.assertIn("habitual_work_department",evaluate_local_law_check("Arrêt maladie en Moselle").missing_facts)
 def test_official_queries_are_required(self): self.assertEqual(3,len(evaluate_local_law_check("Maladie à Sarralbe").source_queries))
