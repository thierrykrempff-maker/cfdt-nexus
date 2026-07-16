import unittest
from datetime import datetime,timezone
from .connector_citation import Citation
from .connector_errors import ConnectorPlatformError,ErrorCode
from .connector_health import HealthReport,HealthStatus
from .connector_logging import LogEntry,LogEventType
from .connector_metadata import ConnectorMetadata
from .connector_models import OperationContext,OperationResult
from .connector_provenance import Provenance
from .connector_statistics import ConnectorStatistics
from .connector_metrics import Metric

NOW=datetime(2026,1,1,tzinfo=timezone.utc)

class ModelTests(unittest.TestCase):
 def test_metadata_valid(self):self.assertEqual("demo",ConnectorMetadata("demo","Demo","Publisher").connector_id)
 def test_metadata_requires_id(self):
  with self.assertRaises(ValueError):ConnectorMetadata("","Demo","Publisher")
 def test_metadata_rejects_punctuation(self):
  with self.assertRaises(ValueError):ConnectorMetadata("bad/id","Demo","Publisher")
 def test_context_valid(self):self.assertEqual("op",OperationContext("demo","op",NOW).operation_id)
 def test_context_requires_timezone(self):
  with self.assertRaises(ValueError):OperationContext("demo","op",datetime(2026,1,1))
 def test_result_refuses_negative_count(self):
  with self.assertRaises(ValueError):OperationResult(True,"OK","",-1)
 def test_citation_valid(self):self.assertEqual("Title",Citation("https://example.invalid/x","Title",None,None,None,"official","UNKNOWN","low").title)
 def test_citation_requires_https(self):
  with self.assertRaises(ValueError):Citation("http://example.invalid","Title",None,None,None,"official","UNKNOWN","low")
 def test_provenance_valid(self):self.assertEqual("demo",Provenance("demo","https://example.invalid",NOW,"abc").source_id)
 def test_provenance_requires_timezone(self):
  with self.assertRaises(ValueError):Provenance("demo","https://example.invalid",datetime(2026,1,1),None)
 def test_log_valid(self):self.assertEqual(LogEventType.VALIDATION,LogEntry(LogEventType.VALIDATION,"demo",NOW,"OK","").event_type)
 def test_log_requires_timezone(self):
  with self.assertRaises(ValueError):LogEntry(LogEventType.ERROR,"demo",datetime(2026,1,1),"ERR","")
 def test_health_valid(self):self.assertEqual(HealthStatus.DISABLED,HealthReport(HealthStatus.DISABLED,NOW).status)
 def test_statistics_default_zero(self):self.assertEqual(0,ConnectorStatistics().document_count)
 def test_statistics_refuse_negative(self):
  with self.assertRaises(ValueError):ConnectorStatistics(document_count=-1)
 def test_metric_valid(self):self.assertEqual("ms",Metric("duration",1.2,"ms").unit)
 def test_metric_requires_name(self):
  with self.assertRaises(ValueError):Metric("",1,"ms")
 def test_platform_error_keeps_code(self):self.assertEqual(ErrorCode.NETWORK_DISABLED,ConnectorPlatformError(ErrorCode.NETWORK_DISABLED,"off").code)
