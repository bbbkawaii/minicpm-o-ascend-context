import unittest

from baseline.benchmark_text import (
    execute_round,
    extract_delta_text,
    RequestMetric,
)
from baseline.metrics import (
    build_metadata,
    compute_itl,
    distribution,
    percentile,
    render_summary,
    RequestError,
)
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

    def test_percentile_requires_values(self):
        with self.assertRaises(ValueError):
            percentile([], 0.5)


class DistributionTests(unittest.TestCase):
    def test_reports_full_five_number_summary(self):
        dist = distribution([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(dist["count"], 4)
        self.assertEqual(dist["mean"], 2.5)
        self.assertEqual(dist["p50"], 2.5)
        self.assertIn("p99", dist)
        self.assertIn("min", dist)
        self.assertIn("max", dist)

    def test_empty_values_marked_unavailable(self):
        dist = distribution([])
        self.assertEqual(dist["count"], 0)
        self.assertIsNone(dist["mean"])


class ItlTests(unittest.TestCase):
    def test_computes_interarrival_latencies(self):
        self.assertEqual(compute_itl([0.1, 0.2, 0.4]), [0.1, 0.2])

    def test_single_sample_has_no_itl(self):
        self.assertEqual(compute_itl([0.1]), [])


class SummarySchemaTests(unittest.TestCase):
    def test_renders_v1_schema_with_errors_and_distributions(self):
        metrics = [
            RequestMetric(0, 0.1, [0.2], 1.0, 10, 5, 0.18),
            RequestMetric(1, 0.3, [], 2.0, 20, None, None),
        ]
        errors = [RequestError(2, "timeout", "request timed out")]
        metadata = build_metadata(
            model="m",
            base_url="http://x/v1",
            requests=3,
            concurrency=1,
            warmup_requests=1,
            prompt="hello",
        )

        summary = render_summary(
            metrics=metrics,
            metric_distributions={
                "ttft_seconds": [m.ttft_seconds for m in metrics],
                "e2e_seconds": [m.e2e_seconds for m in metrics],
            },
            errors=errors,
            wall_seconds=4.0,
            metadata=metadata,
        )

        self.assertEqual(summary["schema_version"], 1)
        self.assertEqual(summary["requests"], 3)
        self.assertEqual(summary["successes"], 2)
        self.assertEqual(summary["failures"], 1)
        self.assertEqual(summary["timeouts"], 1)
        self.assertEqual(summary["success_rate"], round(2 / 3, 6))
        self.assertEqual(summary["request_throughput"], 0.5)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("distributions", summary)
        self.assertIn("run_metadata", summary)


class ErrorIsolationTests(unittest.TestCase):
    def test_partial_failure_keeps_round_and_records_error(self):
        """A failing request must not abort the round; JSON stays parseable."""
        metrics, errors, wall_seconds = execute_round(
            base_url="http://127.0.0.1:9/v1",  # unreachable -> all fail
            model="m",
            prompt="p",
            timeout=0.5,
            requests=2,
            concurrency=1,
            warmup_requests=1,
            request_rate=None,
        )
        self.assertEqual(metrics, [])
        self.assertEqual(len(errors), 3)  # 1 warmup + 2 measured
        self.assertTrue(all(e.kind in ("error", "timeout", "http_error") for e in errors))
        self.assertGreater(wall_seconds, 0.0)

    def test_error_message_is_sanitized_and_truncated(self):
        from baseline.metrics import summarize_error

        long_message = "boom" * 200
        truncated = summarize_error(RuntimeError(long_message))
        self.assertLess(len(truncated), 320)
        self.assertTrue(truncated.endswith("..."))

        err = RequestError(0, "error", truncated)
        rendered = render_summary(
            metrics=[],
            metric_distributions={},
            errors=[err],
            wall_seconds=1.0,
            metadata=build_metadata(
                model="m", base_url="http://x", requests=1,
                concurrency=1, warmup_requests=0, prompt="p",
            ),
        )
        self.assertEqual(len(rendered["errors"]), 1)
        self.assertEqual(rendered["errors"][0]["message"], truncated)


class StabilityTests(unittest.TestCase):
    def test_connection_failures_are_reported(self):
        summary = run_stability("http://127.0.0.1:1/v1", "model", "prompt", 2, 0.01)
        self.assertEqual(summary["requests"], 2)
        self.assertEqual(summary["successes"], 0)
        self.assertEqual(summary["failures"], 2)


if __name__ == "__main__":
    unittest.main()
