import unittest

from baseline.benchmark_text import extract_delta_text, percentile, summarize, RequestMetric
from baseline.smoke_test import extract_message_text
from baseline.stability_test import run_stability


class SmokeTestParsingTests(unittest.TestCase):
    def test_extracts_string_message(self):
        response = {"choices": [{"message": {"content": "ok"}}]}
        self.assertEqual(extract_message_text(response), "ok")

    def test_extracts_structured_message(self):
        response = {
            "choices": [
                {"message": {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}}
            ]
        }
        self.assertEqual(extract_message_text(response), "ab")


class BenchmarkParsingTests(unittest.TestCase):
    def test_extracts_stream_delta(self):
        event = {"choices": [{"delta": {"content": [{"type": "text", "text": "hello"}]}}]}
        self.assertEqual(extract_delta_text(event), "hello")

    def test_percentile_interpolates(self):
        self.assertEqual(percentile([1.0, 2.0, 3.0, 4.0], 0.5), 2.5)

    def test_summary_reports_request_throughput(self):
        metrics = [
            RequestMetric(0, 0.1, 1.0, 10),
            RequestMetric(1, 0.3, 2.0, 20),
        ]
        summary = summarize(metrics, wall_seconds=2.0)
        self.assertEqual(summary["request_throughput"], 1.0)
        self.assertEqual(summary["ttft_seconds"]["p50"], 0.2)


class StabilityTests(unittest.TestCase):
    def test_connection_failures_are_reported(self):
        summary = run_stability("http://127.0.0.1:1/v1", "model", "prompt", 2, 0.01)
        self.assertEqual(summary["requests"], 2)
        self.assertEqual(summary["successes"], 0)
        self.assertEqual(summary["failures"], 2)


if __name__ == "__main__":
    unittest.main()
