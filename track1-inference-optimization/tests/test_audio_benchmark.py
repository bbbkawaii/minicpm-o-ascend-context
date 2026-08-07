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
)
from baseline.metrics import distribution


def make_wav_base64(frame_count=240):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24_000)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return base64.b64encode(wav_buffer.getvalue()).decode()


def make_audio_metric(
    request_id,
    ttft=0.1,
    ttfp=0.4,
    e2e=1.0,
    audio_duration=0.5,
    audio_chunks=2,
    pcm_bytes=480,
    sample_rate=24_000,
    audio_window=0.3,
    icl=None,
    first_pcm=480,
    safe=1.0,
    first_dur=0.25,
    max_gap=0.2,
    chunks=None,
):
    return AudioRequestMetric(
        request_id=request_id,
        ttft_seconds=ttft,
        ttfp_seconds=ttfp,
        e2e_seconds=e2e,
        audio_duration_seconds=audio_duration,
        audio_chunks=audio_chunks,
        pcm_bytes=pcm_bytes,
        sample_rate_hz=sample_rate,
        audio_window_seconds=audio_window,
        icl_seconds=icl if icl is not None else [],
        first_audio_pcm_bytes=first_pcm,
        first_audio_duration_seconds=first_dur,
        max_playback_gap_seconds=max_gap,
        playback_safe_ratio=safe,
        chunks=chunks if chunks is not None else [],
    )


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


class AudioMetricPropertiesTests(unittest.TestCase):
    def test_rtf_boundaries_are_explicit(self):
        metric = make_audio_metric(0, e2e=1.0, audio_duration=0.5, audio_window=0.3)

        self.assertEqual(metric.rtf_e2e, 2.0)
        self.assertEqual(metric.rtf_audio_window, 0.6)


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

        class FakeOpener:
            def open(self, request, timeout=None):
                return fake_urlopen(request, timeout)

        with patch(
            "baseline.benchmark_audio.urllib.request.build_opener",
            return_value=FakeOpener(),
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
        self.assertEqual(metric.first_audio_pcm_bytes, 480)
        self.assertAlmostEqual(metric.playback_safe_ratio, 1.0)

    def test_icl_computed_from_chunk_arrivals(self):
        # Two chunks 0.05s apart each of 0.01s decoded duration => ICL [0.05].
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

        # Patch perf_counter to produce deterministic arrival times.
        times = iter([1.0, 1.05, 1.10, 1.15])
        real_perf_counter = __import__("time").perf_counter

        def fake_perf_counter():
            try:
                return next(times)
            except StopIteration:
                return real_perf_counter()

        def fake_urlopen(request, timeout):
            return FakeResponse()

        class FakeOpener:
            def open(self, request, timeout=None):
                return fake_urlopen(request, timeout)

        with patch("baseline.benchmark_audio.time.perf_counter", side_effect=fake_perf_counter), patch(
            "baseline.benchmark_audio.urllib.request.build_opener",
            return_value=FakeOpener(),
        ):
            metric = run_request(
                8,
                "http://127.0.0.1:8099/v1",
                "model",
                "prompt",
                2.0,
            )

        self.assertEqual(len(metric.icl_seconds), 1)
        self.assertAlmostEqual(metric.icl_seconds[0], 0.05, places=2)


if __name__ == "__main__":
    unittest.main()
