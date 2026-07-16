import unittest
from .connector_backoff import BackoffPolicy
from .connector_cache_policy import CacheMode,CachePolicy
from .connector_deduplication import deduplicate
from .connector_fingerprint import fingerprint_bytes,fingerprint_metadata
from .connector_rate_limit import RateLimitPolicy
from .connector_retry_policy import RetryPolicy
from .connector_scheduler import ScheduleFrequency,SchedulePolicy
from .connector_versioning import DocumentVersion,changed

class PolicyTests(unittest.TestCase):
 def test_rate_limit_allows_below_limit(self):self.assertTrue(RateLimitPolicy(2,60).allows(1))
 def test_rate_limit_blocks_at_limit(self):self.assertFalse(RateLimitPolicy(2,60).allows(2))
 def test_rate_limit_requires_positive(self):
  with self.assertRaises(ValueError):RateLimitPolicy(0,60)
 def test_retry_only_known_code(self):self.assertTrue(RetryPolicy(2,frozenset({"TEMP"})).should_retry(1,"TEMP"))
 def test_retry_stops_at_max(self):self.assertFalse(RetryPolicy(2,frozenset({"TEMP"})).should_retry(2,"TEMP"))
 def test_backoff_exponential(self):self.assertEqual(4,BackoffPolicy(1,2,10).delay(3))
 def test_backoff_is_capped(self):self.assertEqual(3,BackoffPolicy(2,2,3).delay(4))
 def test_backoff_rejects_zero_attempt(self):
  with self.assertRaises(ValueError):BackoffPolicy().delay(0)
 def test_forbidden_cache_has_no_ttl(self):self.assertIsNone(CachePolicy().ttl_seconds)
 def test_forbidden_cache_rejects_ttl(self):
  with self.assertRaises(ValueError):CachePolicy(CacheMode.FORBIDDEN,10)
 def test_temporary_cache_requires_ttl(self):
  with self.assertRaises(ValueError):CachePolicy(CacheMode.TEMPORARY)
 def test_scheduler_never_disabled(self):self.assertFalse(SchedulePolicy().enabled)
 def test_scheduler_cannot_enable(self):
  with self.assertRaises(ValueError):SchedulePolicy(ScheduleFrequency.DAILY,True)
 def test_sha256_is_stable(self):self.assertEqual(fingerprint_bytes(b"x"),fingerprint_bytes(b"x"))
 def test_metadata_fingerprint_is_ordered(self):self.assertNotEqual(fingerprint_metadata(("a","b")),fingerprint_metadata(("b","a")))
 def test_deduplication_reports_duplicate_once(self):self.assertEqual(("a",),deduplicate(["a","a","a"]).duplicate_fingerprints)
 def test_deduplication_preserves_order(self):self.assertEqual(("b","a"),deduplicate(["b","a","b"]).unique_fingerprints)
 def test_versions_detect_change(self):self.assertTrue(changed(DocumentVersion("d","1","a"),DocumentVersion("d","2","b","1")))
 def test_versions_detect_unchanged(self):self.assertFalse(changed(DocumentVersion("d","1","a"),DocumentVersion("d","2","a","1")))
 def test_version_refuses_self_reference(self):
  with self.assertRaises(ValueError):DocumentVersion("d","1","a","1")
