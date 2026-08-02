#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
base_url="${BASE_URL:-http://127.0.0.1:8099/v1}"
model="${MODEL:-openbmb/MiniCPM-o-4_5}"
run_root="${RUN_ROOT:-$repo_root/reports/runs}"
run_id="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-gate1}"
run_dir="$run_root/$run_id"

mkdir -p "$run_dir"
printf '%s\n' "base_url=$base_url" "model=$model" "run_id=$run_id" \
  | tee "$run_dir/gate1-manifest.txt"

BASE_URL="$base_url" \
TIMEOUT_SECONDS="${READY_TIMEOUT_SECONDS:-300}" \
  "$repo_root/baseline/wait_for_ready.sh"

python3 "$repo_root/baseline/smoke_test.py" \
  --base-url "$base_url" \
  --model "$model" \
  | tee "$run_dir/text-smoke.json"

python3 "$repo_root/baseline/stability_test.py" \
  --base-url "$base_url" \
  --model "$model" \
  --requests "${REQUESTS:-20}" \
  --output "$run_dir/stability.json"

printf '%s\n' "Gate 1: PASS; artifacts in $run_dir"
