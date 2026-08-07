#!/usr/bin/env python3
"""Measure text-stream TTFT, ITL, TPOP, and E2E latency.

Emits the shared v1 result schema (see :mod:`baseline.metrics`).  Supports
warm-up requests, error isolation (a failing request does not abort the round),
and an optional fixed request rate.

Metric definitions
------------------
* ttft_seconds    : request start to first non-empty text delta
* itl_seconds     : inter-token latency between consecutive text deltas
* e2e_seconds     : request start to stream completion
* tpot_seconds    : (first delta to completion) / output units (chars or tokens)
* request_throughput : successful requests / wall seconds
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

# Allow running as a standalone script (`python3 baseline/benchmark_text.py`)
# as well as part of the package (`python3 -m unittest ...`), and from a
# copied-elsewhere layout (e.g. `/root/benchmark_text.py` + `/root/metrics.py`).
# Allow running as a standalone script (`python3 baseline/benchmark_text.py`)
# as well as part of the package, and from a copied-elsewhere flat layout
# (e.g. `/root/benchmark_text.py` + `/root/metrics.py`).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_IS_FLAT = os.path.exists(os.path.join(_SCRIPT_DIR, "metrics.py")) and not os.path.isdir(
    os.path.join(_SCRIPT_DIR, "baseline")
)
if _IS_FLAT:
    sys.path.insert(0, _SCRIPT_DIR)
else:
    sys.path.insert(0, os.path.dirname(_SCRIPT_DIR))

if _IS_FLAT:
    from metrics import (  # type: ignore[import-not-found]  # noqa: E402
        RequestError,
        build_metadata,
        compute_itl,
        render_summary,
        summarize_error,
        write_output,
    )
else:
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
    "itl_seconds": "inter-token latency between consecutive text deltas",
    "e2e_seconds": "request start to stream completion",
    "tpot_seconds": "first delta to completion divided by output units",
    "request_throughput": "successful requests per second",
}


@dataclass(frozen=True)
class RequestMetric:
    request_id: int
    ttft_seconds: float
    itl_seconds: list[float]
    e2e_seconds: float
    output_characters: int
    output_tokens: int | None
    tpot_seconds: float | None


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


def extract_usage_tokens(event: dict) -> int | None:
    usage = event.get("usage") or {}
    completion_tokens = usage.get("completion_tokens")
    if isinstance(completion_tokens, int):
        return completion_tokens
    return None


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

    # Benchmarks always target a local inference service. Bypass any
    # http_proxy/https_proxy from the environment so a user proxy config
    # cannot 502 the loopback request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    started = time.perf_counter()
    first_text_at: float | None = None
    delta_arrivals: list[float] = []
    output_parts: list[str] = []
    output_tokens: int | None = None

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
            delta_text = extract_delta_text(event)
            if delta_text:
                if first_text_at is None:
                    first_text_at = now
                delta_arrivals.append(now)
                output_parts.append(delta_text)
            tokens = extract_usage_tokens(event)
            if tokens is not None:
                output_tokens = tokens

    finished = time.perf_counter()
    if first_text_at is None:
        raise RuntimeError(f"request {request_id} completed without a text delta")

    itl = compute_itl(delta_arrivals)
    output_chars = len("".join(output_parts))
    output_units = output_tokens if output_tokens is not None else output_chars
    tpot = (
        (finished - first_text_at) / output_units if output_units > 0 else None
    )

    return RequestMetric(
        request_id=request_id,
        ttft_seconds=first_text_at - started,
        itl_seconds=itl,
        e2e_seconds=finished - started,
        output_characters=output_chars,
        output_tokens=output_tokens,
        tpot_seconds=tpot,
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
) -> tuple[list[RequestMetric], list[RequestError], float]:
    """Run warm-up + measured requests, isolating per-request failures."""
    errors: list[RequestError] = []

    def guarded(request_id: int) -> RequestMetric | None:
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
        except Exception as exc:  # noqa: BLE001 - capture any per-request failure
            errors.append(
                RequestError(
                    request_id=request_id,
                    kind="error",
                    message=summarize_error(exc),
                )
            )
            return None

    # Warm-up: discard results, still count wall time separately.
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        warmup_futures = [
            executor.submit(guarded, request_id)
            for request_id in range(warmup_requests)
        ]
        for future in warmup_futures:
            future.result()

    wall_started = time.perf_counter()
    metrics: list[RequestMetric] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        futures = [
            executor.submit(guarded, request_id)
            for request_id in range(requests)
        ]
        if request_rate is None:
            for future in futures:
                result = future.result()
                if result is not None:
                    metrics.append(result)
        else:
            # Open-loop: submit at a fixed rate, bounded by concurrency.
            interval = 1.0 / request_rate
            for future in futures:
                result = future.result()
                if result is not None:
                    metrics.append(result)
                if request_rate > 0:
                    time.sleep(interval)
    wall_seconds = time.perf_counter() - wall_started
    return metrics, errors, wall_seconds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8099/v1")
    parser.add_argument("--model", default="openbmb/MiniCPM-o-4_5")
    parser.add_argument("--prompt", default="用一句话介绍 MiniCPM-o 4.5。")
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=180)
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

    itl_values: list[float] = []
    for metric in metrics:
        itl_values.extend(metric.itl_seconds)

    summary = render_summary(
        metrics=metrics,
        metric_distributions={
            "ttft_seconds": [m.ttft_seconds for m in metrics],
            "itl_seconds": itl_values,
            "e2e_seconds": [m.e2e_seconds for m in metrics],
            "tpot_seconds": [
                m.tpot_seconds for m in metrics if m.tpot_seconds is not None
            ],
        },
        errors=errors,
        wall_seconds=wall_seconds,
        metadata=metadata,
        metric_definitions=METRIC_DEFINITIONS,
    )

    print(write_output(summary, args.output))
    # A >1% failure rate fails the round but still writes the JSON.
    success_rate = summary["success_rate"]
    if success_rate < 0.99:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
