#!/usr/bin/env python3
"""Parse ``npu-smi info`` output and emit per-device CSV snapshot rows.

Run by :file:`collect_resources.sh` once per tick.  Parsing is done in Python
because the npu-smi table layout (2 lines per NPU: power/temp line then
chip/aicore/hbm line) is awkward to extract with awk.

Output format: ONE ROW PER DEVICE PER TICK.

    timestamp,device_id,npu_aicore_pct,npu_hbm_mb,npu_power_w,npu_temp_c,host_used_kb

device_id is the physical NPU index (e.g. 0, 1).  A metric that cannot be read
is left empty; the summarizer then reports it as ``unavailable``.  Values are
never fabricated as zero.
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


def parse_npu_smi(text: str) -> list[dict[str, str]]:
    """Return one dict per physical NPU with per-device metrics.

    npu-smi packs several values into one table cell, so we parse each data
    line with regexes rather than relying on cell counts.

    Line A: ``| 4     Ascend910 | OK | 170.7  49  0/0 |``
        -> device=4, power=170.7, temp=49
    Line B: ``| 0     8 | 0000:8D:00.0 | 0  0/0  51255/65536 |``
        -> chip=0, aicore=0, hbm=51255

    Line A and Line B are linked by the "NPU" column on line A (the physical
    device group id) and the chip phy-id on line B is the within-group index.
    We pair them by scanning sequentially: after a Line A we expect a Line B.
    """
    devices: list[dict[str, str]] = []
    pending_device: dict[str, str] | None = None

    for line in text.splitlines():
        # Line A: power/temp row, contains "Ascend910"
        #   "| 4     Ascend910 | OK | 170.7  49  0/0 |"
        if "Ascend910" in line:
            cells = [c for c in line.split("|") if c.strip()]
            first_cell = cells[0].split() if cells else []
            device_id = first_cell[0] if first_cell else ""
            # power/temp live in the last cell carrying a numeric payload
            power = temp = ""
            for cell in cells[1:]:
                tokens = cell.split()
                if len(tokens) >= 2:
                    power = _f(tokens[0])
                    temp = _f(tokens[1])
                    break
            pending_device = {
                "device_id": _f(device_id),
                "power": power,
                "temp": temp,
                "aicore": "",
                "hbm": "",
            }
            continue

        # Line B: chip row, e.g. "| 0     8 | 0000:8D:00.0 | 0 0/0 51255/ 65536 |"
        if re.match(r"\|\s*\d+\s+\d+\s*\|", line):
            cells = [c for c in line.split("|") if c.strip()]
            if len(cells) >= 3:
                third = cells[2]
                aicore_m = re.match(r"\s*(\d+\.?\d*)", third)
                aicore = _f(aicore_m.group(1)) if aicore_m else ""
                hbm_m = re.findall(r"(\d+\.?\d*)\s*/\s*\d+\.?\d*", third)
                hbm = _f(hbm_m[-1]) if hbm_m else ""
                if pending_device is not None:
                    pending_device["aicore"] = aicore
                    pending_device["hbm"] = hbm
                    devices.append(pending_device)
                    pending_device = None
            continue

    # If a Line A had no following Line B (incomplete output), drop it.
    return devices


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
        # npu-smi unavailable: emit an empty row so the summarizer marks
        # every metric unavailable. Never fabricate zero values.
        npu_text = ""

    host_kb = host_memory_kb()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    devices = parse_npu_smi(npu_text)

    # At least one row per tick so the collector stays monotonic even when
    # npu-smi is broken; device_id is empty in that case.
    if not devices:
        devices = [
            {
                "device_id": "",
                "power": "",
                "temp": "",
                "aicore": "",
                "hbm": "",
            }
        ]

    for device in devices:
        print(
            ",".join(
                [
                    timestamp,
                    device["device_id"],
                    device["aicore"],
                    device["hbm"],
                    device["power"],
                    device["temp"],
                    host_kb,
                ]
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
