import unittest
from .connector_capabilities import Capability
from .connector_document import DocumentPolicy
from .connector_errors import ErrorCode
from .connector_health import HealthStatus
from .connector_license import LicenseId
from .connector_logging import LogEventType
from .connector_cache_policy import CacheMode
from .connector_scheduler import ScheduleFrequency
from .connector_states import ConnectorState,TRANSITIONS

class EnumTests(unittest.TestCase):pass

def _enum_test(enum_cls,member):
 def test(self):
  self.assertIs(enum_cls(member.value),member);self.assertTrue(str(member.value))
 return test

for enum_cls in (ConnectorState,Capability,DocumentPolicy,ErrorCode,LicenseId):
 for member in enum_cls:
  setattr(EnumTests,f"test_{enum_cls.__name__.lower()}_{member.name.lower()}",_enum_test(enum_cls,member))

class StateGraphTests(unittest.TestCase):
 def test_all_states_have_transition_entry(self):self.assertEqual(set(ConnectorState),set(TRANSITIONS))
 def test_deprecated_is_terminal(self):self.assertEqual(set(),TRANSITIONS[ConnectorState.DEPRECATED])
 def test_enabled_requires_validated_path(self):self.assertIn(ConnectorState.ENABLED,TRANSITIONS[ConnectorState.VALIDATED])
 def test_all_log_events(self):self.assertEqual({"consultation","error","refusal","validation","synchronization","cache"},{item.value for item in LogEventType})
 def test_all_health_states(self):self.assertEqual({"unknown","healthy","degraded","unavailable","disabled"},{item.value for item in HealthStatus})
 def test_all_cache_modes(self):self.assertEqual({"forbidden","temporary","permanent"},{item.value for item in CacheMode})
 def test_all_schedule_frequencies(self):self.assertEqual({"manual","daily","weekly","monthly","never","on_event"},{item.value for item in ScheduleFrequency})
