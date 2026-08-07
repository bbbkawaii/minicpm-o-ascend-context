#!/usr/bin/env python3
"""Summarize resource CSV collected by :file:`collect_resources.sh`.

Usage: summarize_resources.py RESOURCES.csv [--output summary.json]

CSV layout: one row per device per tick with a ``device_id`` column.
The summarizer aggregates per device, reporting peak and p50/p95 for AICore,
HBM, power, and temperature, plus a host-memory peak shared across devices.
A missing value is reported as ``unavailable`` rather than zero, so a broken
collector cannot masquerade as a healthy one.
"""

from __future__ import annotations

import argparse
import csv
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

DEVICE_COLUMNS = {
    "npu_aicore_pct": "npu utilization (%)",
    "npu_hbm_mb": "NPU HBM (MB)",
    "npu_power_w": "NPU power (W)",
    "npu_temp_c": "NPU temperature (C)",
}
HOST_COLUMN = "host_used_kb"


def _parse_float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def summarize_csv(path: Path) -> dict:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(row)

    if not rows:
        return {
            "samples": 0,
            "devices": {},
            "host_used_kb": {"status": "unavailable", "reason": "no samples"},
            "first_timestamp": None,
            "last_timestamp": None,
        }

    timestamps = [row.get("timestamp", "") for row in rows if row.get("timestamp")]

    # Group rows by device_id (empty device_id -> grouped under "").
    by_device: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        device_id = row.get("device_id", "")
        by_device.setdefault(device_id, []).append(row)

    devices_summary: dict[str, dict] = {}
    for device_id, device_rows in by_device.items():
        per_device: dict[str, dict] = {}
        for column, label in DEVICE_COLUMNS.items():
            values = [
                float(v)
                for v in (_parse_float(row.get(column, "")) for row in device_rows)
                if v is not None
            ]
            if not values:
                per_device[column] = {
                    "label": label,
                    "status": "unavailable",
                    "reason": "no parseable values in column",
                }
                continue
            dist = distribution(values)
            per_device[column] = {
                "label": label,
                "status": "ok",
                "peak": round(max(values), 6),
                **dist,
            }
        devices_summary[device_id] = {
            "samples": len(device_rows),
            "metrics": per_device,
        }

    # Host memory: aggregate across all rows (shared system resource).
    host_values = [
        float(v)
        for v in (_parse_float(row.get(HOST_COLUMN, "")) for row in rows)
        if v is not None
    ]
    if host_values:
        host_dist = distribution(host_values)
        host_summary = {
            "label": "host used memory (kB)",
            "status": "ok",
            "peak": round(max(host_values), 6),
            **host_dist,
        }
    else:
        host_summary = {
            "label": "host used memory (kB)",
            "status": "unavailable",
            "reason": "no parseable values in column",
        }

    return {
        "samples": len(rows),
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
        "devices": devices_summary,
        "host_used_kb": host_summary,
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
