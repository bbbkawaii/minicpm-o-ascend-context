#!/usr/bin/env python3
"""Measure MiniCPM-o text and audio streaming latency."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import io
import json
import statistics
import time
import urllib.request
import wave
from dataclasses import asdict, dataclass

if __package__:
    from .benchmark_text import extract_delta_text, percentile
else:
    from benchmark_text import extract_delta_text, percentile


@dataclass(frozen=True)
class WavChunkInfo:
    sample_rate_hz: int
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


def _distribution(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(statistics.fmean(values), 6),
        "p50": round(percentile(values, 0.50), 6),
        "p95": round(percentile(values, 0.95), 6),
    }


def summarize_audio(
    metrics: list[AudioRequestMetric], wall_seconds: float
) -> dict:
    if not metrics:
        raise ValueError("audio summary requires at least one request metric")
    results = []
    for metric in metrics:
        result = asdict(metric)
        result["rtf_e2e"] = round(metric.rtf_e2e, 6)
        result["rtf_audio_window"] = round(metric.rtf_audio_window, 6)
        results.append(result)
    return {
        "metric_definitions": {
            "ttft_seconds": "request start to first non-empty text delta",
            "ttfp_seconds": "request start to first decodable audio WAV delta",
            "e2e_seconds": "request start to stream completion",
            "rtf_e2e": "E2E seconds divided by generated audio duration",
            "rtf_audio_window": (
                "first-to-last audio arrival window divided by generated audio duration"
            ),
        },
        "requests": len(metrics),
        "wall_seconds": round(wall_seconds, 6),
        "request_throughput": round(len(metrics) / wall_seconds, 6),
        "ttft_seconds": _distribution([metric.ttft_seconds for metric in metrics]),
        "ttfp_seconds": _distribution([metric.ttfp_seconds for metric in metrics]),
        "e2e_seconds": _distribution([metric.e2e_seconds for metric in metrics]),
        "audio_duration_seconds": _distribution(
            [metric.audio_duration_seconds for metric in metrics]
        ),
        "rtf_e2e": _distribution([metric.rtf_e2e for metric in metrics]),
        "rtf_audio_window": _distribution(
            [metric.rtf_audio_window for metric in metrics]
        ),
        "results": results,
    }


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

    started = time.perf_counter()
    first_text_at: float | None = None
    first_audio_at: float | None = None
    last_audio_at: float | None = None
    audio_duration = 0.0
    audio_chunks = 0
    pcm_bytes = 0
    sample_rate_hz: int | None = None

    with urllib.request.urlopen(request, timeout=timeout) as response:
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
                audio_duration += chunk.duration_seconds
                audio_chunks += 1
                pcm_bytes += chunk.pcm_bytes
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
    if audio_duration <= 0:
        raise RuntimeError(f"request {request_id} produced zero-duration audio")

    return AudioRequestMetric(
        request_id=request_id,
        ttft_seconds=first_text_at - started,
        ttfp_seconds=first_audio_at - started,
        e2e_seconds=finished - started,
        audio_duration_seconds=audio_duration,
        audio_chunks=audio_chunks,
        pcm_bytes=pcm_bytes,
        sample_rate_hz=sample_rate_hz,
        audio_window_seconds=max(last_audio_at - first_audio_at, 0.0),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8099/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--prompt", default="请用一句中文介绍 MiniCPM-o 4.5。")
    parser.add_argument("--requests", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must be positive")

    wall_started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                run_request,
                request_id,
                args.base_url,
                args.model,
                args.prompt,
                args.timeout,
            )
            for request_id in range(args.requests)
        ]
        metrics = [future.result() for future in futures]
    summary = summarize_audio(metrics, time.perf_counter() - wall_started)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
