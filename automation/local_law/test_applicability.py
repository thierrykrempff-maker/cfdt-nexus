import unittest
from .alsace_moselle_models import EmploymentContext
from .applicability import assess_applicability

class ApplicabilityTests(unittest.TestCase):
 def test_habitual_work_in_moselle(self): self.assertEqual("applicable",assess_applicability(EmploymentContext(habitual_work_department="57")).status)
 def test_moselle_company_worker_outside_zone(self):
  result=assess_applicability(EmploymentContext(habitual_work_department="54",employer_head_office_department="57"));self.assertEqual("not_applicable",result.status);self.assertIn("employer_head_office_alone_is_not_sufficient",result.warnings)
 def test_worker_in_moselle_with_head_office_elsewhere(self): self.assertEqual("applicable",assess_applicability(EmploymentContext(habitual_work_department="Moselle",employer_head_office_department="75")).status)
 def test_unknown_place(self): self.assertEqual("insufficient_information",assess_applicability(EmploymentContext()).status)
 def test_local_establishment_is_not_final_proof(self): self.assertEqual("probably_applicable",assess_applicability(EmploymentContext(establishment_department="67")).status)
 def test_telework_reduces_certainty(self): self.assertEqual("probably_applicable",assess_applicability(EmploymentContext(habitual_work_department="68",telework=True)).status)
 def test_multi_site_is_uncertain(self): self.assertEqual("applicability_uncertain",assess_applicability(EmploymentContext(multiple_work_departments=("57","54"))).status)
 def test_temporary_assignment_is_not_silent(self): self.assertIn("temporary_assignment_requires_duration_and_usual_place",assess_applicability(EmploymentContext(habitual_work_department="57",temporary_assignment=True)).warnings)
