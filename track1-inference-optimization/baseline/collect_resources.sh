#!/usr/bin/env bash
# Collect per-second NPU + host resource snapshots to CSV.
#
# Usage:
#   collect_resources.sh [--interval 1] [--outdir DIR]
#
# Writes:
#   DIR/resources.csv            raw per-second snapshots
#   DIR/collect_resources.pid    collector PID (removed on clean stop)
#
# Stop with SIGTERM/SIGINT (Ctrl-C) or `kill -TERM $(cat ...pid)`.
# On stop, a trailing final snapshot is written so the last sample is not lost.
#
# NPU metrics are parsed by the Python helper (baseline/npu_collect.py), which
# fails to empty fields rather than fabricating zero values when npu-smi is
# unavailable.

set -euo pipefail

INTERVAL=1
OUTDIR="."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval) INTERVAL="$2"; shift 2 ;;
    --outdir)   OUTDIR="$2";  shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUTDIR"
CSV="$OUTDIR/resources.csv"
PIDFILE="$OUTDIR/collect_resources.pid"

COLLECTOR="$SCRIPT_DIR/npu_collect.py"
if [[ ! -f "$COLLECTOR" ]]; then
  # Fall back to a flat-layout copy of the helper next to this script's caller.
  COLLECTOR="$SCRIPT_DIR/npu_collect.py"
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "collect_resources: python3 not found on PATH" >&2
  exit 1
fi

# Write header once.
if [[ ! -s "$CSV" ]]; then
  echo "timestamp,npu_aicore_pct,npu_hbm_mb,npu_power_w,npu_temp_c,host_used_kb" > "$CSV"
fi

snapshot() {
  python3 "$COLLECTOR" >> "$CSV" 2>/dev/null || true
}

echo "$$" > "$PIDFILE"
trap 'snapshot; rm -f "$PIDFILE"; exit 0' TERM INT
trap '' HUP

while true; do
  snapshot
  sleep "$INTERVAL"
done
