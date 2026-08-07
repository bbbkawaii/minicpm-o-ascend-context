import base64
import io
import json
import unittest
import wave
from unittest.mock import patch

from baseline.benchmark_audio import (
    AudioRequestMetric,
    extract_audio_base64,
    inspect_wav_chunk,
    run_request,
    summarize_audio,
)


def make_wav_base64(frame_count=240):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24_000)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return base64.b64encode(wav_buffer.getvalue()).decode()


class AudioEventParsingTests(unittest.TestCase):
    def test_extracts_streamed_audio_from_modality_delta(self):
        event = {
            "modality": "audio",
            "choices": [{"delta": {"content": "UklGRg=="}}],
        }

        self.assertEqual(extract_audio_base64(event), "UklGRg==")

    def test_does_not_treat_text_delta_as_audio(self):
        event = {
            "modality": "text",
            "choices": [{"delta": {"content": "UklGRg=="}}],
        }

        self.assertIsNone(extract_audio_base64(event))

    def test_inspects_24khz_mono_wav_chunk(self):
        info = inspect_wav_chunk(make_wav_base64())

        self.assertEqual(info.sample_rate_hz, 24_000)
        self.assertEqual(info.pcm_bytes, 480)
        self.assertAlmostEqual(info.duration_seconds, 0.01)


class AudioSummaryTests(unittest.TestCase):
    def test_reports_ttfp_and_explicit_rtf_boundaries(self):
        metrics = [
            AudioRequestMetric(0, 0.1, 0.4, 1.0, 0.5, 2, 24_000, 24_000, 0.3),
            AudioRequestMetric(1, 0.3, 0.8, 2.0, 1.0, 4, 48_000, 24_000, 0.9),
        ]

        summary = summarize_audio(metrics, wall_seconds=2.0)

        self.assertEqual(summary["request_throughput"], 1.0)
        self.assertEqual(summary["ttfp_seconds"]["p50"], 0.6)
        self.assertEqual(summary["rtf_e2e"]["p50"], 2.0)
        self.assertEqual(summary["rtf_audio_window"]["p50"], 0.75)


class AudioRequestTests(unittest.TestCase):
    def test_measures_text_and_two_audio_chunks_from_http_stream(self):
        audio_chunk = make_wav_base64()
        events = [
            {"modality": "text", "choices": [{"delta": {"content": "ok"}}]},
            {"modality": "audio", "choices": [{"delta": {"content": audio_chunk}}]},
            {"modality": "audio", "choices": [{"delta": {"content": audio_chunk}}]},
        ]
        lines = [f"data: {json.dumps(event)}\n".encode() for event in events]
        lines.append(b"data: [DONE]\n")

        class FakeResponse:
            def __enter__(self):
                return iter(lines)

            def __exit__(self, *_args):
                return False

        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, 2.0)
            payload = json.loads(request.data)
            self.assertEqual(payload["modalities"], ["text", "audio"])
            return FakeResponse()

        with patch(
            "baseline.benchmark_audio.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            metric = run_request(
                7,
                "http://127.0.0.1:8099/v1",
                "model",
                "prompt",
                2.0,
            )

        self.assertEqual(metric.request_id, 7)
        self.assertEqual(metric.audio_chunks, 2)
        self.assertEqual(metric.pcm_bytes, 960)
        self.assertAlmostEqual(metric.audio_duration_seconds, 0.02)
        self.assertEqual(metric.sample_rate_hz, 24_000)


if __name__ == "__main__":
    unittest.main()
