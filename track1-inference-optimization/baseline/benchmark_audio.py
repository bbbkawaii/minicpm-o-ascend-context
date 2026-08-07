#!/usr/bin/env python3
"""Measure MiniCPM-o text + streaming audio latency.

Emits the shared v1 result schema.  Extends the text benchmark with audio
metrics: TTFP (first audio packet), ICL (inter-chunk latency), audio playback
continuity, and RTF (real-time factor) under two independent definitions.

Metric definitions
------------------
* ttft_seconds          : request start to first non-empty text delta
* ttfp_seconds          : request start to first decodable audio WAV delta
* icl_seconds           : inter-chunk latency between consecutive audio deltas
* e2e_seconds           : request start to stream completion
* audio_duration_seconds: summed decoded audio duration of all chunks
* audio_chunks          : number of decodable audio deltas
* first_audio_pcm_bytes : PCM bytes of the first audio chunk
* rtf_e2e               : E2E seconds / generated audio seconds
* rtf_audio_window      : (first-to-last audio arrival window) / audio seconds
* playback_safe_ratio   : fraction of arrivals where gap <= previous chunk audio
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_IS_FLAT = os.path.exists(os.path.join(_SCRIPT_DIR, "metrics.py")) and not os.path.isdir(
    os.path.join(_SCRIPT_DIR, "baseline")
)
if _IS_FLAT:
    sys.path.insert(0, _SCRIPT_DIR)
else:
    sys.path.insert(0, os.path.dirname(_SCRIPT_DIR))

if _IS_FLAT:
    from benchmark_text import extract_delta_text  # type: ignore[import-not-found]  # noqa: E402
    from metrics import (  # type: ignore[import-not-found]  # noqa: E402
        RequestError,
        build_metadata,
        compute_itl,
        render_summary,
        summarize_error,
        write_output,
    )
else:
    from baseline.benchmark_text import extract_delta_text  # noqa: E402
    from baseline.metrics import (  # noqa: E402
        RequestError,
        build_metadata,
        compute_itl,
        render_summary,
        summarize_error,
        write_output,
    )

METRIC_DEFINITIONS = {
    "ttft_seconds": "request start to first non-empty text delta",
    "ttfp_seconds": "request start to first decodable audio WAV delta",
    "icl_seconds": "inter-chunk latency between consecutive audio deltas",
    "e2e_seconds": "request start to stream completion",
    "audio_duration_seconds": "summed decoded audio duration of all chunks",
    "audio_chunks": "number of decodable audio deltas",
    "first_audio_pcm_bytes": "PCM bytes of the first audio chunk",
    "rtf_e2e": "E2E seconds divided by generated audio duration",
    "rtf_audio_window": (
        "first-to-last audio arrival window divided by generated audio duration"
    ),
    "playback_safe_ratio": (
        "fraction of audio arrivals whose inter-chunk gap does not exceed "
        "the previous chunk's decoded audio duration"
    ),
    "first_audio_duration_seconds": "decoded duration of the first audio chunk",
    "max_playback_gap_seconds": "largest inter-chunk arrival gap in the stream",
}


@dataclass(frozen=True)
class WavChunkInfo:
    sample_rate_hz: int
    pcm_bytes: int
    duration_seconds: float


@dataclass(frozen=True)
class AudioChunkRecord:
    """One decoded audio chunk's arrival evidence."""

    arrival_offset_seconds: float
    pcm_bytes: int
    duration_seconds: float


@dataclass(frozen=True)
class AudioRequestMetric:
    request_id: int
    ttft_seconds: float
    ttfp_seconds: float
    e2e_seconds: float
    audio_duration_seconds: float
    audio_chunks: int
    pcm_bytes: int
    sample_rate_hz: int
    audio_window_seconds: float
    icl_seconds: list[float]
    first_audio_pcm_bytes: int
    first_audio_duration_seconds: float
    max_playback_gap_seconds: float
    playback_safe_ratio: float
    chunks: list[AudioChunkRecord]

    @property
    def rtf_e2e(self) -> float:
        return self.e2e_seconds / self.audio_duration_seconds

    @property
    def rtf_audio_window(self) -> float:
        return self.audio_window_seconds / self.audio_duration_seconds


def extract_audio_base64(event: dict) -> str | None:
    """Return one audio chunk from a supported chat-completion event."""
    choices = event.get("choices") or []
    for choice in choices:
        delta = choice.get("delta") or {}
        audio = delta.get("audio")
        if isinstance(audio, dict) and isinstance(audio.get("data"), str):
            return audio["data"]

        message = choice.get("message") or {}
        audio = message.get("audio")
        if isinstance(audio, dict) and isinstance(audio.get("data"), str):
            return audio["data"]

        if str(event.get("modality", "")).lower() == "audio":
            content = delta.get("content")
            if isinstance(content, str) and content:
                return content
    return None


def inspect_wav_chunk(audio_base64: str) -> WavChunkInfo:
    """Decode one base64 WAV chunk and return its measured audio properties."""
    wav_bytes = base64.b64decode(audio_base64, validate=True)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frame_count = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        pcm_bytes = frame_count * wav_file.getnchannels() * wav_file.getsampwidth()
    return WavChunkInfo(
        sample_rate_hz=sample_rate,
        pcm_bytes=pcm_bytes,
        duration_seconds=frame_count / sample_rate,
    )


def run_request(
    request_id: int,
    base_url: str,
    model: str,
    prompt: str,
    timeout: float,
) -> AudioRequestMetric:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "modalities": ["text", "audio"],
        "chat_template_kwargs": {
            "enable_thinking": False,
            "use_tts_template": True,
        },
        "temperature": 0,
        "max_tokens": 128,
        "stream": True,
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Bypass environment http_proxy/https_proxy: the target is always the
    # local inference service, and a user proxy would 502 the loopback call.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    started = time.perf_counter()
    first_text_at: float | None = None
    first_audio_at: float | None = None
    last_audio_at: float | None = None
    audio_arrivals: list[tuple[float, WavChunkInfo]] = []
    sample_rate_hz: int | None = None

    with opener.open(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            now = time.perf_counter()

            audio_base64 = extract_audio_base64(event)
            if audio_base64:
                chunk = inspect_wav_chunk(audio_base64)
                if sample_rate_hz is None:
                    sample_rate_hz = chunk.sample_rate_hz
                elif sample_rate_hz != chunk.sample_rate_hz:
                    raise RuntimeError(
                        f"request {request_id} changed audio sample rate from "
                        f"{sample_rate_hz} to {chunk.sample_rate_hz}"
                    )
                if first_audio_at is None:
                    first_audio_at = now
                last_audio_at = now
                audio_arrivals.append((now, chunk))
                continue

            if str(event.get("modality", "")).lower() != "audio":
                delta_text = extract_delta_text(event)
                if delta_text and first_text_at is None:
                    first_text_at = now

    finished = time.perf_counter()
    if first_text_at is None:
        raise RuntimeError(f"request {request_id} completed without a text delta")
    if first_audio_at is None or last_audio_at is None or sample_rate_hz is None:
        raise RuntimeError(f"request {request_id} completed without an audio delta")

    audio_duration = sum(chunk.duration_seconds for _, chunk in audio_arrivals)
    if audio_duration <= 0:
        raise RuntimeError(f"request {request_id} produced zero-duration audio")

    pcm_bytes = sum(chunk.pcm_bytes for _, chunk in audio_arrivals)
    first_pcm_bytes = audio_arrivals[0][1].pcm_bytes

    # Inter-chunk latency on arrival times.
    arrival_times = [ts for ts, _ in audio_arrivals]
    icl = compute_itl(arrival_times)

    # Playback safety: a chunk arrives on time if the gap since the previous
    # chunk does not exceed the previous chunk's decoded audio duration.
    safe_count = 0
    comparisons = 0
    max_gap = 0.0
    for i in range(1, len(audio_arrivals)):
        gap = arrival_times[i] - arrival_times[i - 1]
        previous_duration = audio_arrivals[i - 1][1].duration_seconds
        max_gap = max(max_gap, gap)
        comparisons += 1
        if gap <= previous_duration:
            safe_count += 1
    playback_safe_ratio = safe_count / comparisons if comparisons else 1.0

    # Per-chunk evidence, offset relative to the request start.
    chunk_records = [
        AudioChunkRecord(
            arrival_offset_seconds=round(ts - started, 6),
            pcm_bytes=chunk.pcm_bytes,
            duration_seconds=round(chunk.duration_seconds, 6),
        )
        for ts, chunk in audio_arrivals
    ]

    return AudioRequestMetric(
        request_id=request_id,
        ttft_seconds=first_text_at - started,
        ttfp_seconds=first_audio_at - started,
        e2e_seconds=finished - started,
        audio_duration_seconds=audio_duration,
        audio_chunks=len(audio_arrivals),
        pcm_bytes=pcm_bytes,
        sample_rate_hz=sample_rate_hz,
        audio_window_seconds=max(last_audio_at - first_audio_at, 0.0),
        icl_seconds=icl,
        first_audio_pcm_bytes=first_pcm_bytes,
        first_audio_duration_seconds=audio_arrivals[0][1].duration_seconds,
        max_playback_gap_seconds=round(max_gap, 6),
        playback_safe_ratio=round(playback_safe_ratio, 6),
        chunks=chunk_records,
    )


def execute_round(
    *,
    base_url: str,
    model: str,
    prompt: str,
    timeout: float,
    requests: int,
    concurrency: int,
    warmup_requests: int,
    request_rate: float | None,
) -> tuple[list[AudioRequestMetric], list[RequestError], float]:
    measured_errors: list[RequestError] = []

    def guarded(
        request_id: int, errors: list[RequestError]
    ) -> AudioRequestMetric | None:
        try:
            return run_request(
                request_id, base_url, model, prompt, timeout
            )
        except urllib.error.HTTPError as exc:
            errors.append(
                RequestError(
                    request_id=request_id,
                    kind="http_error",
                    message=f"HTTP {exc.code}",
                    http_status=exc.code,
                )
            )
            return None
        except TimeoutError:
            errors.append(
                RequestError(
                    request_id=request_id,
                    kind="timeout",
                    message="request timed out",
                )
            )
            return None
        except Exception as exc:  # noqa: BLE001
            errors.append(
                RequestError(
                    request_id=request_id,
                    kind="error",
                    message=summarize_error(exc),
                )
            )
            return None

    # Warm-up failures are recorded separately so they never pollute the
    # measured success rate or exit code.
    warmup_errors: list[RequestError] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        warmup_futures = [
            executor.submit(guarded, request_id, warmup_errors)
            for request_id in range(warmup_requests)
        ]
        for future in warmup_futures:
            future.result()

    wall_started = time.perf_counter()
    metrics: list[AudioRequestMetric] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        if request_rate is None:
            futures = [
                executor.submit(guarded, request_id, measured_errors)
                for request_id in range(requests)
            ]
            for future in futures:
                result = future.result()
                if result is not None:
                    metrics.append(result)
        else:
            # True open-loop rate: control submit time with a monotonic clock.
            interval = 1.0 / request_rate if request_rate > 0 else 0.0
            next_submit_at = time.monotonic()
            pending: list[concurrent.futures.Future] = []
            for request_id in range(requests):
                now = time.monotonic()
                if interval > 0 and now < next_submit_at:
                    time.sleep(next_submit_at - now)
                pending.append(
                    executor.submit(guarded, request_id, measured_errors)
                )
                next_submit_at = time.monotonic() + interval
            for future in pending:
                result = future.result()
                if result is not None:
                    metrics.append(result)
    wall_seconds = time.perf_counter() - wall_started
    return metrics, measured_errors, wall_seconds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8099/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--prompt", default="请用一句中文介绍 MiniCPM-o 4.5。")
    parser.add_argument("--requests", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--warmup-requests", type=int, default=0)
    parser.add_argument("--request-rate", type=float, default=None)
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must be positive")

    metrics, errors, wall_seconds = execute_round(
        base_url=args.base_url,
        model=args.model,
        prompt=args.prompt,
        timeout=args.timeout,
        requests=args.requests,
        concurrency=args.concurrency,
        warmup_requests=args.warmup_requests,
        request_rate=args.request_rate,
    )

    metadata = build_metadata(
        model=args.model,
        base_url=args.base_url,
        requests=args.requests,
        concurrency=args.concurrency,
        warmup_requests=args.warmup_requests,
        prompt=args.prompt,
    )

    icl_values: list[float] = []
    for metric in metrics:
        icl_values.extend(metric.icl_seconds)

    summary = render_summary(
        metrics=metrics,
        metric_distributions={
            "ttft_seconds": [m.ttft_seconds for m in metrics],
            "ttfp_seconds": [m.ttfp_seconds for m in metrics],
            "icl_seconds": icl_values,
            "e2e_seconds": [m.e2e_seconds for m in metrics],
            "audio_duration_seconds": [m.audio_duration_seconds for m in metrics],
            "audio_chunks": [float(m.audio_chunks) for m in metrics],
            "first_audio_pcm_bytes": [float(m.first_audio_pcm_bytes) for m in metrics],
            "rtf_e2e": [m.rtf_e2e for m in metrics],
            "rtf_audio_window": [m.rtf_audio_window for m in metrics],
            "playback_safe_ratio": [m.playback_safe_ratio for m in metrics],
            "first_audio_duration_seconds": [
                m.first_audio_duration_seconds for m in metrics
            ],
            "max_playback_gap_seconds": [
                m.max_playback_gap_seconds for m in metrics
            ],
        },
        errors=errors,
        wall_seconds=wall_seconds,
        metadata=metadata,
        metric_definitions=METRIC_DEFINITIONS,
    )

    print(write_output(summary, args.output))
    success_rate = summary["success_rate"]
    if success_rate < 0.99:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
