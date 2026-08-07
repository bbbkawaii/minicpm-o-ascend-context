#!/usr/bin/env python3
"""Shared metric types, distributions, and result schema for benchmarks.

The two benchmark CLIs (``benchmark_text``, ``benchmark_audio``) both emit a
uniform result schema defined by :func:`render_summary`.  Keeping the schema
here guarantees text and audio runs produce comparable, machine-readable
output with a single ``schema_version``.

Schema contract (v1):

* Every output carries ``schema_version`` and UTC ``timestamp``.
* Distributions always report count / mean / p50 / p95 / p99 / min / max.
* Errors are stored as sanitized ``RequestError`` records (type + message
  without credentials or request bodies).
* ``run_metadata`` records the environment that produced the numbers.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1

# Patterns that could leak credentials or URL secrets into error messages.
_SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Authorization: Bearer <token> — redact the whole value, including the
    # space-separated bearer token that follows the colon.
    (re.compile(r"(?i)authorization\s*[:=]\s*[^\s,]+(?:\s+[^\s,]+)?", re.IGNORECASE), "authorization=<redacted>"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Bearer <redacted>"),
    (re.compile(r"(?i)(token|password|passwd|secret|api[_-]?key)[\"']?\s*[:=]\s*\S+"), r"\1=<redacted>"),
    (re.compile(r"(?i)gh[ops]_[A-Za-z0-9_]{20,}"), "<token-redacted>"),
    (re.compile(r"(?i)(access[-_]?token|refresh[-_]?token)=[^&\s]+"), r"\1=<redacted>"),
    (re.compile(r"(?i)&?code=[^&\s]+"), "&code=<redacted>"),
)


def _redact_secrets(text: str) -> str:
    """Replace credential-like substrings with placeholders."""
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def summarize_error(exc: BaseException) -> str:
    """Return a sanitized, truncated string describing an exception.

    Credential-like content (authorization headers, tokens, passwords, API
    keys, URL query secrets) is redacted before truncation.
    """
    message = str(exc)
    message = _redact_secrets(message)
    if len(message) > 300:
        message = message[:300] + "..."
    return message


@dataclass(frozen=True)
class RunMetadata:
    """Environment/run facts attached to every benchmark result."""

    model: str
    base_url: str
    requests: int
    concurrency: int
    warmup_requests: int
    prompt_sha256: str
    python_version: str
    schema_version: int = SCHEMA_VERSION
    created_at: str = ""


@dataclass(frozen=True)
class RequestError:
    """A request that failed without aborting the round.

    ``message`` is a sanitized, truncated description.  We never store request
    bodies, tokens, or credentials in results.
    """

    request_id: int
    kind: str
    message: str
    http_status: int | None = None


def prompt_sha256(prompt: str) -> str:
    """Return a short, stable digest of the benchmark prompt."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def percentile(values: list[float], percentile_value: float) -> float:
    """Linear-interpolated percentile, matching numpy's default method."""
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile_value
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def distribution(values: list[float]) -> dict[str, float | int]:
    """Compute a uniform distribution summary over one metric."""
    if not values:
        return {
            "count": 0,
            "mean": None,
            "p50": None,
            "p95": None,
            "p99": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(values),
        "mean": round(statistics.fmean(values), 6),
        "p50": round(percentile(values, 0.50), 6),
        "p95": round(percentile(values, 0.95), 6),
        "p99": round(percentile(values, 0.99), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def compute_itl(arrival_times: list[float]) -> list[float]:
    """Inter-token/chunk latencies from monotonically increasing arrival times."""
    if len(arrival_times) < 2:
        return []
    return [
        round(second - first, 9)
        for first, second in zip(arrival_times, arrival_times[1:])
    ]


def render_summary(
    *,
    metrics: list[Any],
    metric_distributions: dict[str, list[float]],
    errors: list[RequestError],
    wall_seconds: float,
    metadata: RunMetadata,
    metric_definitions: dict[str, str] | None = None,
) -> dict:
    """Compose the v1 result schema from per-request metrics and errors.

    Parameters
    ----------
    metrics
        Per-request metric objects, serialized with :func:`dataclasses.asdict`.
    metric_distributions
        Map of metric name to the list of per-request values for that metric.
    errors
        Sanitized request failures captured during the round.
    wall_seconds
        Wall-clock duration of the round (after warm-up).
    metadata
        Environment metadata for the run.
    metric_definitions
        Optional human-readable definition of each reported metric.
    """
    distributions = {
        name: distribution(values)
        for name, values in metric_distributions.items()
    }
    success_count = len(metrics)
    failure_count = len(errors)
    total = success_count + failure_count
    success_rate = success_count / total if total else 0.0

    # HTTP status distribution across failures (e.g. 429/500/503).
    http_status_counts: dict[int, int] = {}
    for error in errors:
        if error.http_status is not None:
            http_status_counts[error.http_status] = (
                http_status_counts.get(error.http_status, 0) + 1
            )

    summary: dict[str, Any] = {
        "schema_version": metadata.schema_version,
        "created_at": metadata.created_at,
        "model": metadata.model,
        "base_url": metadata.base_url,
        "requests": total,
        "successes": success_count,
        "failures": failure_count,
        "timeouts": sum(1 for e in errors if e.kind == "timeout"),
        "http_status_distribution": http_status_counts,
        "success_rate": round(success_rate, 6),
        "wall_seconds": round(wall_seconds, 6),
        "request_throughput": round(success_count / wall_seconds, 6)
        if wall_seconds > 0
        else None,
        "run_metadata": asdict(metadata),
        "distributions": distributions,
        "errors": [asdict(error) for error in errors],
        "results": [asdict(metric) for metric in metrics],
    }
    if metric_definitions is not None:
        summary["metric_definitions"] = metric_definitions
    return summary


def build_metadata(
    *,
    model: str,
    base_url: str,
    requests: int,
    concurrency: int,
    warmup_requests: int,
    prompt: str,
) -> RunMetadata:
    return RunMetadata(
        model=model,
        base_url=base_url,
        requests=requests,
        concurrency=concurrency,
        warmup_requests=warmup_requests,
        prompt_sha256=prompt_sha256(prompt),
        python_version=f"{__import__('sys').version_info.major}."
        f"{__import__('sys').version_info.minor}",
        created_at=now_utc_iso(),
    )


def write_output(summary: dict, output_path: str | None) -> str:
    """Render the summary as indented JSON and optionally write to a file."""
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(rendered + "\n")
    return rendered
