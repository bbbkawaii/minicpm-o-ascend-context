#!/usr/bin/env python3
"""Summarize resource CSV collected by :file:`collect_resources.sh`.

Usage: summarize_resources.py RESOURCES.csv [--output summary.json]

Emits per-NPU peak and p50/p95 for utilization and HBM, plus host memory peak.
A missing column is reported as ``unavailable`` rather than zero, so a broken
collector cannot masquerade as a healthy one.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
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
    from metrics import distribution, percentile  # type: ignore[import-not-found]  # noqa: E402
else:
    from baseline.metrics import distribution, percentile  # noqa: E402

NUMERIC_COLUMNS = {
    "npu_aicore_pct": "npu utilization (%)",
    "npu_hbm_mb": "NPU HBM (MB)",
    "npu_power_w": "NPU power (W)",
    "npu_temp_c": "NPU temperature (C)",
    "host_used_kb": "host used memory (kB)",
}


def _parse_float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _split_multi(value: str) -> list[float]:
    """npu_aicore_pct may be semicolon-joined per-card: '1;2'."""
    parts = [v.strip() for v in value.split(";") if v.strip()]
    parsed = []
    for part in parts:
        f = _parse_float(part)
        if f is not None:
            parsed.append(f)
    return parsed


def summarize_csv(path: Path) -> dict:
    rows: list[dict[str, float | str]] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(row)

    if not rows:
        return {
            "samples": 0,
            "summary": {
                name: {"status": "unavailable", "reason": "no samples"}
                for name in NUMERIC_COLUMNS
            },
            "first_timestamp": None,
            "last_timestamp": None,
        }

    timestamps = [row.get("timestamp", "") for row in rows if row.get("timestamp")]

    summary: dict = {}
    for column, label in NUMERIC_COLUMNS.items():
        values: list[float] = []
        for row in rows:
            raw = row.get(column, "")
            if column == "npu_aicore_pct":
                values.extend(_split_multi(raw))
            else:
                f = _parse_float(raw)
                if f is not None:
                    values.append(f)
        if not values:
            summary[column] = {
                "label": label,
                "status": "unavailable",
                "reason": "no parseable values in column",
            }
            continue
        dist = distribution(values)
        summary[column] = {
            "label": label,
            "status": "ok",
            "peak": round(max(values), 6),
            **dist,
        }

    return {
        "samples": len(rows),
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="resources.csv from collect_resources.sh")
    parser.add_argument("--output", help="write JSON summary to this file")
    args = parser.parse_args()

    result = summarize_csv(Path(args.csv_path))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(rendered + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
