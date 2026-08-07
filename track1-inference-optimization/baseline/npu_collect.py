#!/usr/bin/env python3
"""Parse ``npu-smi info`` output and emit one CSV snapshot row.

Run by :file:`collect_resources.sh` once per tick.  Parsing is done in Python
because the npu-smi table layout (2 lines per NPU: power/temp line then
chip/aicore/hbm line) is awkward to extract with awk.

Reads ``npu-smi info`` from stdin or from ``NPU_SMI_BIN``.  Output columns:

    timestamp,npu_aicore_pct,npu_hbm_mb,npu_power_w,npu_temp_c,host_used_kb

A single physical NPU contributes one value per metric; multiple NPUs are
joined with ``;`` in the aicore/hbm columns.  A metric that cannot be read is
left empty (the summarizer then reports it as ``unavailable``).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone


def _f(value: str) -> str:
    value = value.strip()
    if not value or value == "-":
        return ""
    return value


def parse_npu_smi(text: str) -> dict[str, str]:
    """Return per-metric semicolon-joined strings for all NPUs in ``text``.

    npu-smi packs several values into one table cell, so we parse each data
    line with regexes rather than relying on cell counts.

    Line A: ``| 4     Ascend910 | OK | 170.7  49  0/0 |``
        -> power=170.7, temp=49
    Line B: ``| 0     8 | 0000:8D:00.0 | 0  0/0  51255/65536 |``
        -> aicore=0, hbm=51255
    """
    metrics: dict[str, list[str]] = {
        "power": [],
        "temp": [],
        "aicore": [],
        "hbm": [],
    }

    for line in text.splitlines():
        # Line A: power/temp row, contains "Ascend910"
        #   "| 4     Ascend910 | OK | 170.7  49  0/0 |"
        if "Ascend910" in line:
            cells = [c for c in line.split("|") if c.strip()]
            # The first cell is "4  Ascend910"; power/temp live in the last
            # cell that carries a numeric payload ("170.7 49 0/0" or "- 51 0/0").
            for cell in cells[1:]:
                tokens = cell.split()
                if len(tokens) >= 2:
                    metrics["power"].append(_f(tokens[0]))
                    metrics["temp"].append(_f(tokens[1]))
                    break
            continue

        # Line B: chip row, e.g. "| 0     8 | 0000:8D:00.0 | 0 0/0 51255/ 65536 |"
        if re.match(r"\|\s*\d+\s+\d+\s*\|", line):
            cells = [c for c in line.split("|") if c.strip()]
            if len(cells) >= 3:
                third = cells[2]
                aicore_m = re.match(r"\s*(\d+\.?\d*)", third)
                if aicore_m:
                    metrics["aicore"].append(_f(aicore_m.group(1)))
                hbm_m = re.findall(r"(\d+\.?\d*)\s*/\s*\d+\.?\d*", third)
                if hbm_m:
                    metrics["hbm"].append(_f(hbm_m[-1]))
            continue

    return {
        "npu_aicore_pct": ";".join(metrics["aicore"]),
        "npu_hbm_mb": ";".join(metrics["hbm"]),
        "npu_power_w": ";".join(metrics["power"]),
        "npu_temp_c": ";".join(metrics["temp"]),
    }


def host_memory_kb() -> str:
    """Return used host memory in kB (total - available) or empty."""
    meminfo = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    meminfo[parts[0].rstrip(":")] = int(parts[1])
        total = meminfo.get("MemTotal")
        available = meminfo.get("MemAvailable")
        if total is not None and available is not None:
            return str(total - available)
    except OSError:
        pass
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--npu-smi-bin", default="npu-smi")
    args = parser.parse_args()

    try:
        result = subprocess.run(
            [args.npu_smi_bin, "info"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        npu_text = result.stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # npu-smi unavailable or errored: emit an empty row (summarizer marks
        # it unavailable), never fabricate zero values.
        npu_text = ""

    parsed = parse_npu_smi(npu_text)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    row = ",".join(
        [
            timestamp,
            parsed["npu_aicore_pct"],
            parsed["npu_hbm_mb"],
            parsed["npu_power_w"],
            parsed["npu_temp_c"],
            host_memory_kb(),
        ]
    )
    print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
