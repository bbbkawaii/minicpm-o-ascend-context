#!/usr/bin/env python3
"""Measure text-stream TTFT and E2E latency through the OpenAI-compatible API."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import statistics
import time
import urllib.request
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RequestMetric:
    request_id: int
    ttft_seconds: float
    e2e_seconds: float
    output_characters: int


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile_value
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def extract_delta_text(event: dict) -> str:
    choices = event.get("choices") or []
    if not choices:
        return ""
    content = choices[0].get("delta", {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return ""


def run_request(
    request_id: int,
    base_url: str,
    model: str,
    prompt: str,
    timeout: float,
) -> RequestMetric:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "modalities": ["text"],
        "chat_template_kwargs": {
            "enable_thinking": False,
            "use_tts_template": False,
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
    output_parts: list[str] = []
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            delta_text = extract_delta_text(event)
            if delta_text:
                if first_text_at is None:
                    first_text_at = time.perf_counter()
                output_parts.append(delta_text)

    finished = time.perf_counter()
    if first_text_at is None:
        raise RuntimeError(f"request {request_id} completed without a text delta")
    return RequestMetric(
        request_id=request_id,
        ttft_seconds=first_text_at - started,
        e2e_seconds=finished - started,
        output_characters=len("".join(output_parts)),
    )


def summarize(metrics: list[RequestMetric], wall_seconds: float) -> dict:
    ttft = [metric.ttft_seconds for metric in metrics]
    e2e = [metric.e2e_seconds for metric in metrics]
    return {
        "requests": len(metrics),
        "wall_seconds": round(wall_seconds, 6),
        "request_throughput": round(len(metrics) / wall_seconds, 6),
        "ttft_seconds": {
            "mean": round(statistics.fmean(ttft), 6),
            "p50": round(percentile(ttft, 0.50), 6),
            "p95": round(percentile(ttft, 0.95), 6),
        },
        "e2e_seconds": {
            "mean": round(statistics.fmean(e2e), 6),
            "p50": round(percentile(e2e, 0.50), 6),
            "p95": round(percentile(e2e, 0.95), 6),
        },
        "results": [asdict(metric) for metric in metrics],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8099/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--prompt", default="用一句话介绍 MiniCPM-o 4.5。")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=180)
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
    summary = summarize(metrics, time.perf_counter() - wall_started)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
