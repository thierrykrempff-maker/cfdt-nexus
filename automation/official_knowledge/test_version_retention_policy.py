import unittest
from datetime import datetime,timedelta,timezone
from automation.official_knowledge.document_policy_models import VersionState
from automation.official_knowledge.document_retention import RetentionPolicy,deletion_decision
from automation.official_knowledge.version_policy import compare_version,mark_current,mark_historical

class VersionRetentionTests(unittest.TestCase):
 def test_new_and_unchanged_version(self):
  first=compare_version("s","https://official.example/a","synthetic");self.assertEqual(VersionState.NEW_VERSION,first.state)
  same=compare_version("s","https://official.example/a","synthetic",first.content_sha256,first.version_id);self.assertEqual(VersionState.UNCHANGED,same.state);self.assertEqual(first.version_id,same.version_id)
 def test_current_and_history(self):
  d=compare_version("s","https://official.example/a","synthetic");self.assertEqual(VersionState.CURRENT,mark_current(d).state);self.assertEqual(VersionState.HISTORICAL,mark_historical(d).state)
 def test_never_delete_journal_provenance_fingerprint(self):
  now=datetime.now(timezone.utc);policy=RetentionPolicy(timedelta(0),True)
  for artifact in ("sync_journal","provenance","fingerprint"):self.assertFalse(deletion_decision(artifact,now=now,created_at=now-timedelta(days=1),policy=policy).allowed)
 def test_delete_content_only_by_policy(self):
  now=datetime.now(timezone.utc);created=now-timedelta(days=10)
  self.assertFalse(deletion_decision("cached_content",now=now,created_at=created,policy=RetentionPolicy(timedelta(days=1),False)).allowed)
  self.assertTrue(deletion_decision("cached_content",now=now,created_at=created,policy=RetentionPolicy(timedelta(days=1),True)).allowed)
