import tempfile
import unittest
from pathlib import Path

from api.domain.telemetry import RequestMetric
from api.infrastructure.telemetry_repository import SqliteTelemetryRepository


class TelemetryTests(unittest.TestCase):
    def test_repository_aggregates_request_metrics_without_payload_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            repository = SqliteTelemetryRepository(Path(folder) / "metrics.db")
            repository.record(RequestMetric("GET", "/api/v1/menu", 200, 12.5))
            repository.record(RequestMetric("GET", "/api/v1/menu", 503, 27.5))

            stats = repository.statistics()

        self.assertEqual(stats["requests_total"], 2)
        self.assertEqual(stats["errors_total"], 1)
        self.assertEqual(stats["average_duration_ms"], 20.0)
        self.assertEqual(stats["by_route"][0]["route"], "/api/v1/menu")
        self.assertNotIn("body", stats)
        self.assertNotIn("ip", stats)

    def test_metric_rejects_queries_and_non_api_paths(self):
        for route in ("/api/v1/menu?secret=value", "/health"):
            with self.assertRaises(ValueError):
                RequestMetric("GET", route, 200, 1)


if __name__ == "__main__":
    unittest.main()
