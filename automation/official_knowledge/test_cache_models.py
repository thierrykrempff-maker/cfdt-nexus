import unittest
from datetime import datetime,timezone
from automation.official_knowledge.cache_models import CacheEntry

class CacheModelTests(unittest.TestCase):
 def test_relative_cache_model(self):
  c=CacheEntry("synthetic","https://official.example/a","f",datetime.now(timezone.utc),"architecture-only",relative_local_path="CACHE/synthetic/item.json")
  self.assertEqual("pending",c.validation_state);self.assertFalse(c.relative_local_path.startswith("C:"))
 def test_absolute_cache_path_refused(self):
  with self.assertRaises(ValueError):CacheEntry("s","https://official.example","f",datetime.now(timezone.utc),"v",relative_local_path="C:/secret")
