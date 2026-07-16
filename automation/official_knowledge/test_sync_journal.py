import unittest
from automation.official_knowledge.rate_limit import RateLimitPolicy,backoff_seconds,minimum_interval,should_stop
from automation.official_knowledge.sync_journal import blocked_run,planned_run

class SyncTests(unittest.TestCase):
 def test_planned_and_stable(self):
  a=planned_run("synthetic","none","2026-01-01");b=planned_run("synthetic","none","2026-01-01");self.assertEqual("planned",a.status);self.assertEqual(a.sync_run_id,b.sync_run_id)
 def test_blocked(self):
  run=blocked_run("synthetic","none","x");self.assertEqual("blocked",run.status);self.assertIn("NETWORK_DISABLED_BY_DEFAULT",run.errors)
 def test_rate_calculations_do_not_sleep(self):
  p=RateLimitPolicy(max_requests_per_minute=30,minimum_delay_seconds=1,max_attempts=3);self.assertEqual(2,minimum_interval(p));self.assertEqual(4,backoff_seconds(p,3));self.assertTrue(should_stop(p,3,0))
