import unittest
from .subject_registry import RULES,rules_for

class RegistryTests(unittest.TestCase):
 def test_l1226_articles_are_distinct(self):
  ids={r.local_rule_id for r in RULES};self.assertIn("AM-WAGE-L1226-23",ids);self.assertIn("AM-WAGE-L1226-24",ids)
 def test_no_fixed_duration_or_entitlement(self):
  payload=" ".join(str(r.to_dict()) for r in RULES).casefold();self.assertNotIn("six semaines",payload);self.assertNotIn("6 semaines",payload)
 def test_personal_cause_concepts_are_kept(self): self.assertIn("cause_personnelle_independante_de_la_volonte",rules_for("employment_contract_suspension")[0].applicability_conditions)
 def test_good_friday_needs_municipality(self): self.assertIn("municipality_information_required",next(r for r in RULES if r.local_rule_id=="AM-HOLIDAY-GOOD-FRIDAY").warnings)
 def test_holiday_is_not_automatically_paid_nonworking(self): self.assertIn("holiday_status_does_not_prove_paid_non_working_day",next(r for r in RULES if r.local_rule_id=="AM-HOLIDAY-DEC26").warnings)
 def test_notice_is_not_investigated(self): self.assertEqual("not_investigated",next(r for r in RULES if r.local_rule_id=="AM-NOTICE").current_status)
 def test_other_matters_are_not_investigated(self): self.assertEqual("not_investigated",next(r for r in RULES if r.local_rule_id=="AM-OTHER").current_status)
