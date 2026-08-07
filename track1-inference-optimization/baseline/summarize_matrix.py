#!/usr/bin/env python3
"""Aggregate a benchmark matrix into a steady-state summary.

Reads the per-cell ``benchmark.json`` files written by
:file:`run_benchmark_matrix.sh` and aggregates the measured (non-cold-start)
rounds into one per-concurrency summary per label.  Round 0 (cold start) is
excluded from the steady-state numbers.

Usage:
    summarize_matrix.py RUNS_DIR [--output summary.json]

RUNS_DIR layout (produced by run_benchmark_matrix.sh):

    <label>/conc<N>/round<R>/benchmark.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_IS_FLAT = os.path.exists(os.path.join(_SCRIPT_DIR, "metrics.py")) and not os.path.isdir(
    os.path.join(_SCRIPT_DIR, "baseline")
)
if _IS_FLAT:
    sys.path.insert(0, _SCRIPT_DIR)
else:
    sys.path.insert(0, os.path.dirname(_SCRIPT_DIR))

if _IS_FLAT:
    from metrics import distribution  # type: ignore[import-not-found]  # noqa: E402
else:
    from baseline.metrics import distribution  # noqa: E402


def aggregate_metric(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "status": "no_data"}
    dist = distribution(values)
    dist["status"] = "ok"
    return dist


def summarize_matrix(runs_dir: Path) -> dict:
    labels: dict[str, dict] = {}

    for label_dir in sorted(runs_dir.iterdir()):
        if not label_dir.is_dir():
            continue
        label = label_dir.name
        concurrency_entries: dict[str, dict] = {}

        for conc_dir in sorted(label_dir.iterdir(), key=lambda p: int(p.name[4:])):
            if not conc_dir.is_dir() or not conc_dir.name.startswith("conc"):
                continue
            conc = conc_dir.name  # "conc1", "conc2", ...

            # Collect benchmark.json from steady-state rounds (round >= 1).
            per_metric: dict[str, list[float]] = {}
            successes = 0
            failures = 0
            rounds_used = 0
            for round_dir in sorted(
                conc_dir.glob("round*"), key=lambda p: int(p.name[5:])
            ):
                round_num = int(round_dir.name[5:])
                if round_num < 1:
                    continue  # exclude cold-start round 0
                bench_file = round_dir / "benchmark.json"
                if not bench_file.exists():
                    continue
                with open(bench_file, encoding="utf-8") as f:
                    data = json.load(f)
                successes += data.get("successes", 0)
                failures += data.get("failures", 0)
                rounds_used += 1
                for metric_name, dist in (data.get("distributions") or {}).items():
                    values = per_metric.setdefault(metric_name, [])
                    # Distribution may carry a summary; reconstruct per-request
                    # values from the results list instead for exactness.
                    values.extend(
                        m.get(metric_name, 0.0)
                        for m in (data.get("results") or [])
                        if isinstance(m, dict) and isinstance(m.get(metric_name), (int, float))
                    )

            aggregated = {
                name: aggregate_metric(values)
                for name, values in per_metric.items()
            }
            total_attempted = successes + failures
            concurrency_entries[conc] = {
                "rounds": rounds_used,
                "successes": successes,
                "failures": failures,
                "attempted": total_attempted,
                "success_rate": round(successes / total_attempted, 6)
                if total_attempted
                else None,
                "metrics": aggregated,
            }

        labels[label] = concurrency_entries

    return {"labels": labels}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_dir", help="matrix RUNS_DIR from run_benchmark_matrix.sh")
    parser.add_argument("--output", help="write JSON summary to this file")
    args = parser.parse_args()

    result = summarize_matrix(Path(args.runs_dir))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
