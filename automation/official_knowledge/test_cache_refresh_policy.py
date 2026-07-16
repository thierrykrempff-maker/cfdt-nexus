import unittest
from datetime import datetime,timedelta,timezone
from automation.official_knowledge.document_cache_policy import CachePolicy,allow_cache,expires_at,is_expired
from automation.official_knowledge.document_policy_models import CacheMode,RefreshMode
from automation.official_knowledge.license_policy import license_capabilities
from automation.official_knowledge.refresh_policy import RefreshPolicy,next_refresh,refresh_due

class CacheRefreshTests(unittest.TestCase):
 def test_cache_forbidden_temporary_permanent(self):
  open_license=license_capabilities("CC_BY")
  self.assertFalse(allow_cache(CachePolicy(CacheMode.FORBIDDEN,None),open_license).allowed)
  self.assertTrue(allow_cache(CachePolicy(CacheMode.TEMPORARY,timedelta(days=1)),open_license).allowed)
  self.assertTrue(allow_cache(CachePolicy(CacheMode.PERMANENT,None),open_license).allowed)
 def test_license_can_refuse_cache_or_permanent(self):
  self.assertFalse(allow_cache(CachePolicy(CacheMode.TEMPORARY,timedelta(days=1)),license_capabilities("UNKNOWN")).allowed)
  self.assertFalse(allow_cache(CachePolicy(CacheMode.PERMANENT,None),license_capabilities("CC_BY_NC")).allowed)
 def test_expiration(self):
  stored=datetime(2026,1,1,tzinfo=timezone.utc);p=CachePolicy(CacheMode.TEMPORARY,timedelta(days=1));self.assertEqual(stored+timedelta(days=1),expires_at(stored,p));self.assertTrue(is_expired(stored+timedelta(days=2),stored,p))
 def test_refresh_modes(self):
  base=datetime(2026,1,1,tzinfo=timezone.utc)
  self.assertEqual(base+timedelta(days=1),next_refresh(base,RefreshPolicy(RefreshMode.DAILY)))
  self.assertEqual(base+timedelta(days=7),next_refresh(base,RefreshPolicy(RefreshMode.WEEKLY)))
  self.assertEqual(base+timedelta(days=30),next_refresh(base,RefreshPolicy(RefreshMode.MONTHLY)))
  self.assertIsNone(next_refresh(base,RefreshPolicy(RefreshMode.MANUAL)));self.assertIsNone(next_refresh(base,RefreshPolicy(RefreshMode.NEVER)))
 def test_event_refresh(self):
  p=RefreshPolicy(RefreshMode.ON_EVENT,"publication");now=datetime.now(timezone.utc);self.assertTrue(refresh_due(now,None,p,event="publication"));self.assertFalse(refresh_due(now,None,p,event="other"))
